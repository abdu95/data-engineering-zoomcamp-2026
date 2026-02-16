import os 
import sys 
import gzip
import shutil
from concurrent.futures import ThreadPoolExecutor 
from google.cloud import storage 
from google.api_core.exceptions import NotFound, Forbidden 
import time 
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BUCKET_NAME = "mod-04-analytics-bucket"
CREDENTIALS_FILE = "gcs.json"
client = storage.Client.from_service_account_json(CREDENTIALS_FILE)

TAXI = "green"
YEAR = "2020"
BASE_URL = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{TAXI}/{TAXI}_tripdata_{YEAR}-"
MONTHS = [f"{i:02d}" for i in range(1, 13)]
DOWNLOAD_DIR = "csv_files"

CHUNK_SIZE = 8 * 1024 * 1024 
TIMEOUT = 300  # 5 minutes timeout
MAX_DOWNLOAD_RETRIES = 3

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bucket = client.bucket(BUCKET_NAME)


def get_session():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def download_file(month):
    """Download and decompress .csv.gz file"""
    url = f"{BASE_URL}{month}.csv.gz"
    gz_file_path = os.path.join(DOWNLOAD_DIR, f"{TAXI}_tripdata_{YEAR}-{month}.csv.gz")
    csv_file_path = os.path.join(DOWNLOAD_DIR, f"{TAXI}_tripdata_{YEAR}-{month}.csv")

    # Skip if already downloaded and decompressed
    if os.path.exists(csv_file_path):
        print(f"File already exists: {csv_file_path}, skipping download")
        return csv_file_path

    for attempt in range(MAX_DOWNLOAD_RETRIES):
        try:
            print(f"Downloading {url} (Attempt {attempt + 1}/{MAX_DOWNLOAD_RETRIES})...")
            
            session = get_session()
            
            # Download the .gz file with timeout
            response = session.get(url, stream=True, timeout=TIMEOUT)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(gz_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"Progress for month {month}: {progress:.1f}%", end='\r')
            
            print(f"\nDownloaded: {gz_file_path}")
            
            # Decompress the file
            print(f"Decompressing {gz_file_path}...")
            with gzip.open(gz_file_path, 'rb') as f_in:
                with open(csv_file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the .gz file to save space
            os.remove(gz_file_path)
            
            print(f"Decompressed: {csv_file_path}")
            return csv_file_path
            
        except requests.exceptions.Timeout:
            print(f"\nTimeout downloading {url} (attempt {attempt + 1})")
            if os.path.exists(gz_file_path):
                os.remove(gz_file_path)
            if attempt < MAX_DOWNLOAD_RETRIES - 1:
                wait_time = 10 * (attempt + 1)
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            
        except Exception as e:
            print(f"\nFailed to download {url}: {e}")
            if os.path.exists(gz_file_path):
                os.remove(gz_file_path)
            if attempt < MAX_DOWNLOAD_RETRIES - 1:
                wait_time = 10 * (attempt + 1)
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    print(f"Failed to download month {month} after {MAX_DOWNLOAD_RETRIES} attempts")
    return None 


def create_bucket(bucket_name):
    try:
        bucket = client.get_bucket(bucket_name)
        
        # check if bucket is among project buckets 
        project_bucket_ids = [bckt.id for bckt in client.list_buckets()]
        if bucket_name in project_bucket_ids:
            print(
                f"Bucket '{bucket_name}' exists and belongs to your project. Proceeding..."
            )
        else:
            print(
                f"A bucket with the name '{bucket_name}' already exists, but it does not belong to your project."
            )
            sys.exit(1)
    
    except NotFound:
        # if the bucket does not exist, create it
        bucket = client.create_bucket(bucket_name) 
        print(f"Created bucket '{bucket_name}' ")
    except Forbidden:
        # bucket exists but no access 
        print(
            f"A bucket with name '{bucket_name}' exists, but it is not accessible. Bucket name is taken. Try different bucket name"
        )
        sys.exit(1)


def verify_gcs_upload(blob_name):
    return storage.Blob(bucket=bucket, name=blob_name).exists(client)


def upload_to_gcs(file_path, max_retries=3):
    if file_path is None:
        return False
        
    blob_name = os.path.basename(file_path)
    blob = bucket.blob(blob_name)
    blob.chunk_size = CHUNK_SIZE

    create_bucket(BUCKET_NAME)

    for attempt in range(max_retries):
        try: 
            print(f"Uploading {file_path} to {BUCKET_NAME} (Attempt {attempt + 1})... ")
            blob.upload_from_filename(file_path)
            print(f"Uploaded: gs://{BUCKET_NAME}/{blob_name}")

            if verify_gcs_upload(blob_name):
                print(f"Verification successful for {blob_name}")
                return True
            else:
                print(f"Verification failed for {blob_name}, retrying...")
        except Exception as e:
            print(f"Failed to upload {file_path} to GCS: {e}")

        time.sleep(5)

    print(f"Giving up on {file_path} after {max_retries} attempts.")
    return False


if __name__ == "__main__":
    create_bucket(BUCKET_NAME)

    print("Starting downloads...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        file_paths = list(executor.map(download_file, MONTHS))

    successful_downloads = [fp for fp in file_paths if fp is not None]
    print(f"\nSuccessfully downloaded {len(successful_downloads)}/{len(MONTHS)} files")

    print("\nStarting uploads to GCS...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(upload_to_gcs, file_paths))

    successful_uploads = sum(1 for r in results if r)
    print(f"\nAll files processed. Successfully uploaded {successful_uploads}/{len(MONTHS)} files")
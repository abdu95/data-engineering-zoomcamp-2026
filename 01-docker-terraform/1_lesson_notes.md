
Docker for Data Engineering: Postgres, Docker Compose, and Real-World Workflows - Alexey Grigorev

## 1 Run pipeline in CLI  
Pipeline

pipeline folder + pipeline.py

`python pipeline.py 13`
run script with args 


`print("arguments", sys.argv)`
shows args that was passed while running the script 


## 2 Run pipeline using uv

`uv` - a modern, fast Python package and project manager written in Rust. It's much faster than pip and handles virtual environments automatically.

`pip install uv`

Now initialize a Python project with uv:

`uv init --python=3.13`

This creates a pyproject.toml file for managing dependencies and a .python-version file.

`uv run python -V`

virt env has different Python version than host machine 


Now let's add pandas:

`uv add pandas pyarrow`

run python script: 

`uv run python pipeline.py 10`


## 3 Run pipeline in Docker image 

We create Docker image from Dockerfile and run pipeline inside the container

create file Dockerfile - it contains all instructions to create image 


```Dockerfile
# base Docker image that we will build on
FROM python:3.13.11-slim

# set up our image by installing prerequisites; pandas in this case
RUN pip install pandas pyarrow

# set up the working directory inside the container
WORKDIR /app
# copy the script to the container. 1st name is source file, 2nd is destination
COPY pipeline.py pipeline.py

# define what to do first when the container runs
# in this example, we will just run the script
ENTRYPOINT ["python", "pipeline.py"]
```

build the image 
`docker build -t test:pandas .`

enter the container
`docker run -it --entrypoint=bash --rm test:pandas`

inside bash of container:
`python pipeline.py 11`

now parquet file is created inside the container. 

But instead of manually running this command in bash, we can use ENTRYPOINT command in Dockerfile



uv inside the container

Container can contain many apps. But using uv inside a container can ensure that a specific app has its own isolated Python environment. 


## 4 PostgreSQL in Docker image 



```bash
docker run -it --rm -e POSTGRES_USER=root -e POSTGRES_PASSWORD=root -e POSTGRES_DB=ny_taxi -v ny_taxi_postgres_data:/var/lib/postgresql -p 5432:5432 postgres:18
```

- -e sets environment variables (user, password, database name)
- -v ny_taxi_postgres_data:/var/lib/postgresql 
creates volume internal to Docker

    - Docker manages this volume automatically
    - Data persists even after container is removed
    - Volume is stored in Docker's internal storage

- -p 5432:5432 maps port 5432 from container to host (port mapping)
- postgres:18 uses PostgreSQL version 18 (latest as of Dec 2025)


`uv add --dev pgcli`

dev dependencies - dependencies that are needed only for dev

`uv run pgcli -h localhost -p 5432 -u root -d ny_taxi`

pgcli is inside the virt env of host. It connects to db in Docker using port 5432. 

Note: make sure no other service is running in port 5432

`\dt` - show tables 



`CREATE TABLE  test (id INTEGER, name VARCHAR(50));`


`INSERT INTO test VALUES (1, 'Hello Docker');`


## 5 Ingest CSV into Postgres

- create a notebook script 
- get data from Github
- ingest data to Postgres using SqlAlchemy


`uv add --dev jupyter`

`uv run jupyter notebook`

Script in notebook to ingest data to postgres

Preview NYC Taxi data: 

```python
import pandas as pd

# Read a sample of the data
prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
df = pd.read_csv(prefix + 'yellow_tripdata_2021-01.csv.gz')

# Display first rows
df.head()

# Check data types
df.dtypes

# Check data shape
df.shape

```

read_csv() shows: 

*DtypeWarning: Columns (0: store_and_fwd_flag) have mixed types. Specify dtype option on import or set low_memory=False.*

Also, when column has integer and also NaN, pandas assigns float64 data type. 

- CSV - schemaless. types are unknown 
- parquet - has schema assigned in parquet file

```python

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

df = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    dtype=dtype,
    parse_dates=parse_dates
)
```

`uv add sqlalchemy psycopg2-binary`

used to connect pandas to db  


```
from sqlalchemy import create_engine
user = 'root'
password = 'root'
engine = create_engine('postgresql://' + user + ':' + password + '@localhost:5432/ny_taxi')
```

define user, port, db



define schema

`print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))`

create table 

`df.head(0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')`


Add tqdm to see progress:

`uv add tqdm`

`from tqdm.auto import tqdm`


divide data into chunks

```python
df_iter = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=100000
)

```
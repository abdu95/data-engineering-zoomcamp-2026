from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql.functions import col
import datetime
import os


spark = SparkSession.builder \
    .master("local[*]") \
    .appName("nyc_taxi") \
    .getOrCreate()

df = spark.read.parquet("data/yellow_tripdata_2025-11.parquet")

### QUESTION 2 START

# Repartition to 4 and save
# df.repartition(4).write.mode("overwrite").parquet("data/yellow_tripdata_2025-11_repartitioned")

# # Calculate average size of the generated .parquet files
# output_dir = "data/yellow_tripdata_2025-11_repartitioned"

# parquet_files = [
#     f for f in os.listdir(output_dir)
#     if f.endswith(".parquet")
# ]

# sizes_mb = [
#     os.path.getsize(os.path.join(output_dir, f)) / (1024 * 1024)
#     for f in parquet_files
# ]

# avg_size_mb = sum(sizes_mb) / len(sizes_mb)

# print(f"Number of parquet files: {len(parquet_files)}")
# print(f"Individual sizes (MB): {[round(s, 3) for s in sizes_mb]}")
# # 25MB
# print(f"Average parquet file size: {avg_size_mb:.3f} MB")

### QUESTION 2 END

### QUESTION 3 

# df = df.select('*', sf.to_date(df.tpep_pickup_datetime).alias("pickup_date"))
# # 162 604
# print(df.filter(df.pickup_date == '2025-11-15').count())


### QUESTION 4 

# df = df.select('*', (col("tpep_dropoff_datetime") - col("tpep_pickup_datetime") ).alias("duration"))
# # 90.6
# df.select(sf.max(df.duration).cast("long") / 3600).show()

### QUESTION 5

lookup_csv = spark.read.csv("data/taxi_zone_lookup.csv", header = True)
df_zone_count = df.groupBy("PULocationID").agg(sf.count("*").alias("trip_count"))

# Governor's Island/Ellis Island/Liberty Island
df_zone_count.join(lookup_csv, df_zone_count.PULocationID == lookup_csv.LocationID, "inner") \
                    .sort(sf.asc("trip_count")) \
                    .show()

print(df.count())

input("Press Enter to stop")
spark.stop()
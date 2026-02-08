## Lesson 3: Data Warehousing & BigQuery


### Data

For this homework we will be using the Yellow Taxi Trip Records for January 2024 - June 2024 (not the entire year of data).

Load 6 files into your GCS bucket

You will need to use the PARQUET option when creating an external table.


### BigQuery Setup
Create an external table using the Yellow Taxi Trip Records.

- I wanted to create via UI but I received error: 
*Bucket names may only contain lowercase letters, numbers, dashes, underscores, and dots.*


```sql
CREATE OR REPLACE EXTERNAL TABLE `mod-03-data-warehouse.mod_03_dataset.yellow_taxi_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://mod-03-dwh_bucket/*.parquet']
);
```


Question 1 


Create a (regular/materialized) table in BQ using the Yellow Taxi Trip Records (do not partition or cluster this table).

```sql
CREATE OR REPLACE TABLE `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart` AS 
SELECT * FROM  `mod-03-data-warehouse.mod_03_dataset.yellow_taxi_external`;
```

What is count of records for the 2024 Yellow Taxi Data?

select count(*)
from `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart` ;


20 332 093


Question 2

Write a query to count the distinct number of PULocationIDs for the entire dataset on both the tables.

What is the estimated amount of data that will be read when this query is executed on the External Table and the Table?



```sql
select count(distinct PULocationID)
from `mod-03-data-warehouse.mod_03_dataset.yellow_taxi_external`;

select count(distinct PULocationID)
from `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart` ;
```

0 MB for the External Table and 155.12 MB for the Materialized Table

Question 3 

Write a query to retrieve the PULocationID from the table (not the external table) in BigQuery. Now write a query to retrieve the PULocationID and DOLocationID on the same table.

Why are the estimated number of Bytes different?

```SQL 
select PULocationID from mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart ; 

-- this showed 155.12 MB 

select PULocationID, DOLocationID from mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart ; 

-- this showed 310.24 MB
```


BigQuery stores data in columnar format, not row format.

Think of table like this internally:

column: PULocationID     → stored separately
column: DOLocationID     → stored separately
column: fare_amount      → stored separately
...


When you run: SELECT PULocationID FROM table


BigQuery reads only one column file.


Question 4. Counting zero fare trips
How many records have a fare_amount of 0?


```sql
select count(*)
from `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart` 
where fare_amount = 0;
```


Question 5. Partitioning and clustering

What is the best strategy to make an optimized table in Big Query if your query will always filter based on tpep_dropoff_datetime and order the results by VendorID (Create a new table with this strategy)

Anwswer: Partition by tpep_dropoff_datetime and Cluster on VendorID


here is the thing that shows difference between partition & clustering:

- clustering sorts data inside each partition


Why this is correct

Your query pattern:

always filters by tpep_dropoff_datetime

always orders by VendorID

In BigQuery optimization:

Rule 1 — Partition by filtering column

If queries filter by date/time:

WHERE tpep_dropoff_datetime BETWEEN ...


Then BigQuery should scan only relevant partitions.

So: PARTITION BY DATE(tpep_dropoff_datetime)


This dramatically reduces scanned data.

Rule 2 — Cluster by column used for sorting/grouping

If queries often:

ORDER BY VendorID
GROUP BY VendorID
WHERE VendorID = ...

Then cluster by that column.

Clustering:

- sorts data inside each partition
- reduces scan time
- speeds aggregations and ordering

So: CLUSTER BY VendorID


Why other options are wrong

❌ Cluster by both

Cluster on tpep_dropoff_datetime and VendorID


Clustering is not a replacement for partitioning. Date filtering without partition = expensive.

❌ Partition by VendorID

Partitioning should be on:

date
ingestion time
logical time column

Partitioning by VendorID is bad because:

low cardinality
uneven distribution
bad performance

❌ Partition by both columns

BigQuery allows only: one partition column (not multiple)

new table with partition and cluster: 

```sql 
CREATE OR REPLACE TABLE `mod-03-data-warehouse.mod_03_dataset.yellow_trip_part_clust`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID
AS
SELECT *
FROM `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart`;
```


Question 6. Partition benefits
Write a query to retrieve the distinct VendorIDs between tpep_dropoff_datetime 2024-03-01 and 2024-03-15 (inclusive)

Use the materialized table you created earlier in your from clause and note the estimated bytes. Now change the table in the from clause to the partitioned table you created for question 5 and note the estimated bytes processed. What are these values?

```sql 
select distinct VendorID
from `mod-03-data-warehouse.mod_03_dataset.yellow_trip_nonpart` 
where tpep_dropoff_datetime between '2024-03-01' AND '2024-03-15';
```

Estimated bytes: 310.24 MB


```sql 
select distinct VendorID
from `mod-03-data-warehouse.mod_03_dataset.yellow_trip_part_clust`
where tpep_dropoff_datetime between '2024-03-01' AND '2024-03-15';
```
Estimated bytes: 26.84 MB


Question 7: Where is the data stored in the External Table you created?

Big Query
Container Registry
GCP Bucket
Big Table

GCP Bucket



External tables in BigQuery do NOT store data inside BigQuery.

They only store:

- metadata (schema, location, format)
- pointer to files

The actual data stays in: Google Cloud Storage (GCS bucket). BigQuery just reads from that bucket when you query.

❌ Native tables store data in BigQuery
✔ External tables only **reference** external storage

- Where is data stored for external tables?
- In the underlying storage system such as Google Cloud Storage. BigQuery only stores metadata and reads the data at query time.


Question 8. Clustering best practices


It is best practice in Big Query to always cluster your data: True/False

❌ False

It is not best practice to always cluster. Clustering is useful only when it matches your query patterns.

When clustering IS useful

Use clustering if you frequently:

filter by a column
group by a column
order by a column
join on a column

Example:

WHERE VendorID = 2
GROUP BY VendorID
ORDER BY VendorID


Then:
CLUSTER BY VendorID


makes queries faster and cheaper.


When clustering is NOT useful

Do NOT cluster if:

table is small (<1 GB usually)
queries don’t filter/group by that column
high-cardinality random column rarely used
you don’t have consistent query patterns

Clustering adds:

extra storage organization work
maintenance overhead
no benefit if not used in queries


Partitioning and clustering should be driven by: How the table is queried, not by habit

Clustering should only be used when queries frequently filter or aggregate on specific columns. Otherwise it provides no benefit and can add overhead.
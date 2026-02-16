## Lesson 4: Analytics Engineering

Goal: Transforming the data loaded in DWH into Analytical Views developing a dbt project.


Prerequisites For Cloud Setup (BigQuery):

Completed Module 3: Data Warehouse with:
- A GCP project with BigQuery enabled
- Service account with BigQuery permissions. Least privileges: 
    - BigQuery Data Editor 
    - BigQuery Job User
    - BigQuery User
- NYC taxi data loaded into BigQuery (yellow and green taxi data for 2019-2020)

download parquet files to GCS bucket > create dataset in BigQuery > load data from GCS bucket to BigQuery dataset

```sql
LOAD DATA INTO  `mod-04-analytics.nytaxi.yellow_tripdata`
FROM FILES (
  format = 'CSV',
  uris = ['gs://mod-04-analytics-bucket/yellow_tripdata*'],
  skip_leading_rows = 1
);

LOAD DATA INTO  `mod-04-analytics.nytaxi.green_tripdata`
FROM FILES (
  format = 'CSV',
  uris = ['gs://mod-04-analytics-bucket/green_tripdata*'],
  skip_leading_rows = 1
);
```

The airport_fee type mismatch is happening because you're using the Parquet files from the official NYC TLC website. Those files have inconsistent column types across different months (e.g., airport_fee is INT32 in some files and DOUBLE in others).

For Module 4, you should download the data from the DataTalksClub NYC TLC Data repository instead.

https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{TAXI}/{TAXI}_tripdata_{YEAR}-




dbt Platform (prev. dbt Cloud)

- create New Project
- connection: BigQuery
- upload JSON file
- Studio
    - Connection: BigQuery
    - dataset: dbt_dataset
        In development, dbt will build your models into a dataset with this name
    - Set up a repo: Github
    - open Studio
    - init project


### 4.3.2 

dbt ==> models => staging: sources.yml
- database = GCP project ID
- schema = dataset name

```yml
version: 2

sources: 
  - name: raw_data
    database: mod-04-analytics
    description: "Raw data sources for NYC taxi rides"
    schema: nytaxi 
    tables: 
      - name: yellow_tripdata
      - name: green_tripdata
```

- staging model to get data in raw layer: 

```sql
with tripdata as (
  select *
  from {{ source('staging','green_tripdata') }}
  where vendorid is not null 
),

renamed as (
  select
      -- identifiers
      cast(vendorid as integer) as vendorid,
      cast(ratecodeid as integer) as ratecodeid,
      cast(pulocationid as integer) as pickup_locationid,
      cast(dolocationid as integer) as dropoff_locationid,
      
      -- timestamps
      cast(lpep_pickup_datetime as timestamp) as pickup_datetime,
      cast(lpep_dropoff_datetime as timestamp) as dropoff_datetime,
      
      -- trip info
      store_and_fwd_flag,
      cast(passenger_count as integer) as passenger_count,
      cast(trip_distance as numeric) as trip_distance,
      cast(trip_type as integer) as trip_type,
      
      -- payment info
      cast(fare_amount as numeric) as fare_amount,
      cast(extra as numeric) as extra,
      cast(mta_tax as numeric) as mta_tax,
      cast(tip_amount as numeric) as tip_amount,
      cast(tolls_amount as numeric) as tolls_amount,
      cast(ehail_fee as numeric) as ehail_fee,
      cast(improvement_surcharge as numeric) as improvement_surcharge,
      cast(total_amount as numeric) as total_amount,
      cast(payment_type as integer) as payment_type,
      {{ get_payment_type_description('payment_type') }} as payment_type_description
  from tripdata
)

select * from renamed

```

- taxi_rides_ny - name of source. name parameter in source.yml file
- green_tripdata - name of the table 


Up until now we've been using `{{ source() }}` to pull in raw data. But that's **only** for things declared in your sources YAML — i.e. raw tables that live outside of dbt.

If the input to your model is **another dbt model**, you use `{{ ref() }}` instead.

- `{{ source('name', 'table') }}` → raw data defined in your YAML
- `{{ ref('model_name') }}` → another dbt model


- .sql files should be SAVED. Otherwise, dbt run does not recognize files


### 4.4.2 

- How to enrich column payment_type?

In macros: 

```jinja2
{% macro get_payment_type(payment_type_column) %}
    CASE {{ payment_type_column }}
    {% set payment_types = dbt_utils.get_column_values(table=ref('payment_type_lookup'), column='payment_type') %}
    {% set descriptions = dbt_utils.get_column_values(table=ref('payment_type_lookup'), column='description') %}
    {% for i in range(payment_types | length) %}
        WHEN {{ payment_types[i] }} THEN '{{ descriptions[i] }}'
    {% endfor %}
        ELSE 'Unknown'
    END
{% endmacro %}
```

Inside the model:

`{{ get_payment_type('payment_type') }} AS payment_type`


- Dulicate rows count: 383 588

```sql 
SELECT 
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(
    CAST(vendor_id AS STRING),
    CAST(pickup_datetime AS STRING),
    CAST(pickup_location_id AS STRING),
    CAST(dropoff_location_id AS STRING)
  )) AS distinct_rows,
  COUNT(*) - COUNT(DISTINCT CONCAT(
    CAST(vendor_id AS STRING),
    CAST(pickup_datetime AS STRING),
    CAST(pickup_location_id AS STRING),
    CAST(dropoff_location_id AS STRING)
  )) AS duplicate_rows
FROM `mod-04-analytics.dbt_dataset.int_trips_unioned`;
```


- Show each duplicate: 

```sql
SELECT 
  vendor_id,
  pickup_location_id,
  dropoff_location_id,
  pickup_datetime,
  dropoff_datetime,
  COUNT(*) AS duplicate_count
FROM `mod-04-analytics.dbt_dataset.int_trips_unioned`
GROUP BY 
  vendor_id,
  pickup_location_id,
  dropoff_location_id,
  pickup_datetime,
  dropoff_datetime
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```



### 4.5.1

- Add description to yml file 

`dbt docs generate`

didn't work on dbt Platform 

- opens web page of documentation 
`dbt docs serve` 


### 4.5.2.

Test types:

- Singular tests
- Source freshness: dbt source freshness
- Generic tests: unique, not null, accepted values, relationship
- Custom generic tests
- Unit tests
- Model contracts 
- CI pipelines 



### 4.5.3.

packages.yml

```
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
```

- Install: 

`dbt deps`

### 4.6.1

dbt inti: creates dbt directories
dbt debug: checks if connection is valid 
dbt seed: loads csv files 
dbt snapshot: 
dbt source freshness: after setting freshnes rules in in yml file, checks if data is stale
dbt docs generate: generates json file which used to build dbt documentation as website after running =>
dbt docs serve
dbt clean: gets rid of whatever declared in clean-targets:        
  - "target"
  - "dbt_packages"
dbt compile: takes models - compiles
dbt run: materializes models (default: view)
dbt test: runs all tests 
dbt build: dbt run + dbt test + dbt seed + dbt snapshot + UDFs
dbt --help
dbt --version
dbt run --full-refresh: if incremental model exists, it uploads data from scratch
dbt run --fail-fast
dbt test -t prod: run in prod, not dev
dbt run --select stg_green_tripdata: runs only this model
dbt run --select +int_trips_unioned: build upstream model that int_trips_unioned depends on
dbt run --select int_trips_unioned+: build int_trips_unioned and all downstream models that depends on it
dbt run --select state:modified => modified status is mentioned in manifest.json 



- Why is there no target folder in the dbt Platform?
- The target/ folder does exist in dbt Cloud, but it's hidden from the file explorer by default.
Why it's hidden:
    The target/ folder contains compiled SQL and temporary artifacts
    dbt Cloud hides it to keep the file tree clean and focused on your source code
    It's regenerated every time you run dbt commands, so it's not meant to be edited


### Homework

Q3: 

select count(*)
from `mod-04-analytics.dbt_dataset.fct_monthly_zone_revenue`;

Q4:


select pickup_zone, SUM(revenue_monthly_total_amount)
from `mod-04-analytics.dbt_dataset.fct_monthly_zone_revenue`
where service_type = 'Green'
group by pickup_zone
order by 2 DESC;


Q5:

select SUM(total_monthly_trips)
from `mod-04-analytics.dbt_dataset.fct_monthly_zone_revenue`
where service_type = 'Green'
AND revenue_month = '2019-10-01';

Q6:

```sql
LOAD DATA INTO  `mod-04-analytics.nytaxi.fhv_tripdata_2019`
FROM FILES (
  format = 'CSV',
  uris = ['gs://mod-04-analytics-bucket/fhv_tripdata*'],
  skip_leading_rows = 1
);
```
# Data Engineering Zoomcamp 

## Homework 1: Docker, SQL and Terraform 


### Question 1. What's the version of pip in the python:3.13 image? (1 point)

- Get python image, enter the container and open bash
`docker run -it --rm python:3.13 bash`

- Check pip version inside the container
`pip --version`

**Answer:** 25.3 


### Question 2. Understanding Docker networking and docker-compose

Given the following docker-compose.yaml, what is the hostname and port that pgadmin should use to connect to the postgres database?

```yaml
services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
      POSTGRES_DB: 'ny_taxi'
    ports:
      - '5433:5432'
    volumes:
      - vol-pgdata:/var/lib/postgresql/data

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: "pgadmin@pgadmin.com"
      PGADMIN_DEFAULT_PASSWORD: "pgadmin"
    ports:
      - "8080:80"
    volumes:
      - vol-pgadmin_data:/var/lib/pgadmin

volumes:
  vol-pgdata:
    name: vol-pgdata
  vol-pgadmin_data:
    name: vol-pgadmin_data

```


**Answer:** postgres:5432


### Question 3. Counting short trips 

Prepare the Data

- Download the green taxi trips data for November 2025:

wget https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-11.parquet


- the dataset with zones:

wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv


```SQL
select count(*) 
from green_tripdata_2025_11 
where lpep_pickup_datetime >= '2025-11-01' 
    AND lpep_pickup_datetime < '2025-12-01' AND trip_distance <=1
```

**Answer:** 8,007


### Question 4. Longest trip for each day


```sql
select lpep_pickup_datetime, trip_distance 
from green_tripdata_2025_11 
where trip_distance < 100 order by 2 desc;
```

+----------------------+---------------+
| lpep_pickup_datetime | trip_distance |
|----------------------+---------------|
| 2025-11-14 15:36:27  | 88.03         |

**Answer:** 2025-11-14


### Question 5. Biggest pickup zone


```sql

SELECT
    pu."Zone" AS pickup_zone,
    SUM(gt.total_amount) AS total_amount_sum
FROM green_tripdata_2025_11 gt
JOIN taxi_zone_lookup pu
    ON pu."LocationID" = gt."PULocationID"
WHERE gt.lpep_pickup_datetime >= '2025-11-18'
  AND gt.lpep_pickup_datetime <  '2025-11-19'
GROUP BY pu."Zone"
ORDER BY total_amount_sum DESC
LIMIT 1;

```

**Answer:**  East Harlem North


### Question 6. Largest tip


```sql
select dof."Zone" as drop_off_zone, gt.tip_amount
from green_tripdata_2025_11 gt
left join taxi_zone_lookup pu
    ON pu."LocationID" = gt."PULocationID"
left join taxi_zone_lookup dof
    ON dof."LocationID" = gt."DOLocationID"
where lpep_pickup_datetime >= '2025-11-01' AND lpep_pickup_datetime < '2025-12-01'
    AND  pu."LocationID" = (select "LocationID" from taxi_zone_lookup where "Zone" = 'East Harlem North')
order by tip_amount desc;
```


**Answer:** Yorkville West 

### Question 7. Terraform Workflow

Which of the following sequences, respectively, describes the workflow for:

1. Downloading the provider plugins and setting up backend,
2. Generating proposed changes and auto-executing the plan
3. Remove all resources managed by terraform`

Answers:

* terraform import, terraform apply -y, terraform destroy
* teraform init, terraform plan -auto-apply, terraform rm
* terraform init, terraform run -auto-approve, terraform destroy
* terraform init, terraform apply -auto-approve, terraform destroy
* terraform import, terraform apply -y, terraform rm

**Answer:** terraform init, terraform apply -auto-approve, terraform destroy

## Lesson 2: Workflow Orchestration

Kestra 

is an open-source, infinitely-scalable orchestration platform that enables all engineers to manage business-critical workflows.

We create `docker-compose.yml` file. 

- Question: Kestra and postgres using same image but we are creating separate database for each inside the same image?

You are using the same Docker image (postgres:18), but you are not sharing one Postgres instance or one database. You are running two completely separate Postgres containers, each with its own data volume and its own database(s).


A Docker image is just a blueprint.
A Docker container is a running instance of that blueprint.

You use the same blueprint twice:

```
pgdatabase:
  image: postgres:18

kestra_postgres:
  image: postgres:18

```

This means:

Same Postgres version

Same base configuration

Same binaries

But once containers start, they live separate lives.


We'll set up Kestra using Docker Compose containing one container for the Kestra server and another for the Postgres database:


```
cd 02-workflow-orchestration
docker compose up -d
```

Note: Check that pgAdmin isn't running on the same ports as Kestra. If so, check out the FAQ at the bottom of the README.

Once the container starts, you can access the Kestra UI at http://localhost:8080.


-d stands for detached mode.

- Containers start in the background
- Terminal is immediately free
- Containers keep running even if you close the terminal
- No logs shown automatically. without -d Logs stream directly into your terminal



To shut down Kestra, go to the same directory and run the following command:

`docker compose down`


### 2.2.2 - Kestra Concepts

Flow (workflow)
 └─ Tasks
     └─ Task Runner


Workflow consists of tasks. Tasks has properties. We can pass data between tasks using outputs.

Workflow cannot be edited after we press SAVE. 


Question: task runner

taskRunner answers one specific question: Where and how should this task actually run? in what execution environment.

- input - we can click Exeecute and fill input 

We can use input as expression: 

`{{inputs.name}}`

- We can pass input to a variable 

`{{render(vars.welcome_message)}}`

This renders input first => then variable

- outputs: Return task


use output:
`{{outputs.generate_output.value}}`

- triggers: task Schedule (can be event too)

- concurrency: how many of such workflows can run at the same time


### 2.3.2 Pipeline: Load Taxi Data to Postgres

We use NY Taxi data 2019-2021:
https://github.com/DataTalksClub/nyc-tlc-data/releases


`04_postgres_taxi.yaml`

- inputs:
We add three inputs: taxi type (yellow or green), year, month. We store yellow and green taxi data into separate tables. 


- variables:

=> We ask user to fill input
=> Based on input we create variable
=> Based on variable we create labels

- extract task:

we use wget to download files from GitHub

taskRunner: defines where to run the task

Runs the task as a local process on the Kestra machine.

```
taskRunner:
  type: io.kestra.plugin.core.runner.Process
```


- postgresql task:

=> create_table
=> create_staging_table
=> truncate_staging_table 
=> copy_in_to_staging_table
=> add_unique_id_and_filename
=> merge a table with staging table 


- Question: 

I just executed it for 2019 January green_trip data. what if I excute again, new data will be appended or existing data overwritten?

No, its not overwritten. We generate unique_row_key based on column values. Next time we generate this unique_row_key based on same column values, it will be the same. so when we reach INSERT, since new generated unique_row_key and unique_row_key in the table is the same, INSERT is not executed. INSERT is executed only when new generated unique_row_key and existing unique_row_key in the table does not MATCH 


```sql
MERGE INTO target T
USING staging S
ON T.unique_row_id = S.unique_row_id
WHEN NOT MATCHED THEN
  INSERT ...

```

Note: after workflow is edited, dont forget to click Save button

after extract task U added the following task to check the size of the file for Question 1:


```yml
  - id: check_file_size
    type: io.kestra.plugin.scripts.shell.Commands
    taskRunner:
      type: io.kestra.plugin.core.runner.Process
    commands:
      - ls -lh {{render(vars.file)}}
```

Thoughts about Kestra:
- I liked Gantt view - horizontal Execute view of Kestra. It is more user-friendly than Airflows vertical bars. 
- Kestra needs Stop button to interrupt workflow mannually. 
- I dont like to embed Python code into YML markdown file 


### 2.3.3 Scheduling and Backfills

We create flow with trigger. Then define schedule when this will trigger: 


```yml
variables:
  file: "{{inputs.taxi}}_tripdata_{{trigger.date | date('yyyy-MM')}}.csv"
  staging_table: "public.{{inputs.taxi}}_tripdata_staging"
  table: "public.{{inputs.taxi}}_tripdata"
  data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ (trigger.date | date('yyyy-MM')) ~ '.csv']}}"

triggers:
  - id: green_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"
    inputs:
      taxi: green

  - id: yellow_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 10 1 * *"
    inputs:
      taxi: yellow
```

Now we can use this trigger for backfill. Backfil is going to previous time when this schedule would have run and fetching data for that previous date. 




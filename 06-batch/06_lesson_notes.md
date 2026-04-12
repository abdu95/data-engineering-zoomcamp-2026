

.parquet format: 
- it knows schema
- more efficient compressing


LAZY EVALUATION
TRANSFORMATIONS VS ACTIONS 

    TRANSFORMATIONS
        not executed immediately
        
        NARROW TRANSFORMATION (NO DATA SHUFFLE) 
        WIDE TRANSFORMATION (DATA SHUFFLE)
        
        withColumn() - repartition

    ACTIONS
        executed immediately 

        show()
        head()
        take()


Virtual Machine in GCP 

.sh - bash file 
wget - download file from internet 

registerTempTable()
    before executing SQL in PySpark, you should execute this function on dataframe 


CLIENT
    DRIVER 
    SparkContext 

STANDALONE CLUSTER
    MASTER
    ClusterManager

    WORKER
    Executor
    Task | Task


RDD
    Resilient Distributed Dataset 
    RDDs are fault-tolerant, immutable data structures in Apache Spark enabling parallel processing.

- upload files to GCS
Spark.read(gs://)_

*.jar* = contains functions to connect to GCS
*gcs.json* = contains login, pass

create local Spark cluster


notebook => to script (to use outside the notebook)

*argparse* -  Parser for command-line options, arguments 

Library => Class => Instance => Property => Function

- Spark master: defines executor
- SparkSubmit - submits job to cluster 
    start cluster mannually

stop-slave
stop-master

Run Spark in Cloud
Cluster in GCP

DataProc - Create Cluster
    DataProc already knows how to connect to GCP

Virtual Machine in GCP
upload .py file to Google Cloud 

We used GCP UI. But we can also use SDK (e.g. for Airflow)


Spark installation:
- Java
- pyspark

Problem: 
it seems I already have spark set in env var. I removed it and pyspark worked fine.

You have SPARK_HOME=C:\spark set somewhere, but Spark is not installed there. PySpark is trying to use an external Spark installation instead of its bundled one.

Found it using this:

```python
import os
os.environ["JAVA_HOME"] = r"C:\Java\jdk-21"
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\Java\jdk-21\bin;C:\hadoop\bin;" + os.environ["PATH"]

# Monkey-patch Popen to print the command before running
import subprocess
original_popen = subprocess.Popen
def debug_popen(cmd, **kwargs):
    print("POPEN COMMAND:", cmd)
    return original_popen(cmd, **kwargs)
subprocess.Popen = debug_popen

from pyspark.sql import SparkSession
spark = SparkSession.builder \
    .master("local[*]") \
    .appName('test') \
    .getOrCreate()
```

it showed this:

POPEN COMMAND: ver
POPEN COMMAND: ['C:\\spark\\./bin/spark-submit.cmd', '--conf', 'spark.master=local[*]', '--conf', 'spark.app.name=test', 'pyspark-shell']


Homework

Question 2: partition

* now my question is we had parquet file which was 70MB and when we partitioned, why we got 4 partitions approximately 25MB each?
* what partition actually is in Spark and why we use it?


Why 4 × 25 MB instead of 4 × ~17.5 MB?
You might expect 70 MB ÷ 4 = ~17.5 MB, but that's not how it works. The original single .parquet file is compressed. When Spark reads it into memory, it decompresses the data — the in-memory size is much larger than 70 MB. When it writes 4 new parquet files, each partition is compressed independently and may use a different compression ratio than the original. So the total output (4 × 25 = 100 MB) being larger than the input (70 MB) is completely normal.


What is a partition in Spark?
A partition is simply a chunk of your data that lives in memory on one executor (worker). Think of it like splitting a big spreadsheet into smaller pieces so multiple people can work on them simultaneously.
When you have 4 partitions:

Spark assigns each partition to a CPU core
All 4 cores process their chunk in parallel
Results are combined at the end

Without partitioning, one core would process all the data sequentially — much slower.

Why do we use partitions?
Three main reasons:

Parallelism — more partitions = more cores working simultaneously = faster processing
Memory management — instead of loading 70 MB (or much more when decompressed) into one core, each core handles a manageable chunk
Scalability — on a real cluster with 100 machines, 400 partitions means each machine handles just a small slice of the data


The general rule of thumb is 2-4 partitions per CPU core. For local development like yours local[*] uses all your cores, so 4 partitions is a sensible starting point.


Video: How I'd Learn Spark FAST (2026)
https://www.youtube.com/watch?v=_ii08GBoIcY&t=4s

CLIENT
    DRIVER 
    SparkContext 

STANDALONE CLUSTER
    MASTER
    ClusterManager

    WORKER
    Executor
    Task | Task

How ResourceManager distribute the work?

LAZY EVALUAUTION
    TRANSFORMATIONS
        NARROW TRANSFORMATION (NO DATA SHUFFLE)
        WIDE TRANSFORMATION (DATA SHUFFLE)
    ACTIONS

DATAFRAME API
    Operations:
        df = spark.read.csv()
        df.show()
        df.select()
        df.withColumnRenamed()
        df.withColumn()
        df.drop()
        df.filter()
        df.sort()

SPARK SQL 
    SPARK BY EXAMPLES

INTERVIEW
    INTERVIEWBIT - SPARK questions




Claude conversation:

how would you teach Spark? 
I want to learn it but I dont know how to start. why spark was intended? which problem it solves and in which stage of data workflow is it used? what are its fundamental concepts?

# Apache Spark — From First Principles

---

## 1. The Problem Spark Was Built to Solve

To understand Spark, you need to understand what came before it.

**The pre-2000s world:** Data fit on one machine. You ran SQL on a database, got your answer, done.

**The 2000s problem:** The internet exploded. Companies like Google, Yahoo, Facebook started generating data at a scale that *no single machine could process*. A single server has maybe 256GB RAM and 64 CPU cores. What do you do when your dataset is 10TB?

**The answer: distribute the work across hundreds of machines.**

Google published a paper in 2004 describing **MapReduce** — a programming model where you split data across many machines, process each chunk in parallel (*Map*), then combine the results (*Reduce*). Yahoo open-sourced this as **Hadoop MapReduce**.

**But Hadoop had a brutal problem:**

Every single step of a computation had to write its intermediate results to disk (HDFS). So a multi-step job looked like:

```
Read from disk → Process → Write to disk → Read from disk → Process → Write to disk → ...
```

A complex machine learning job with 100 iterations would hit disk 200 times. This made it **painfully slow** — think hours for jobs that should take minutes.

**Spark was born in 2009 at UC Berkeley to fix exactly this.**

The core insight: *keep data in memory (RAM) across steps instead of writing to disk every time.*

```
Hadoop:  Disk → RAM → Disk → RAM → Disk → RAM → Disk   (slow)
Spark:   Disk → RAM → RAM → RAM → RAM → RAM → Disk      (fast, up to 100x)
```

---

## 2. Where Spark Sits in the Data Workflow

You know the modern data stack well. Here's where Spark lives:

```
Raw Data Sources
  (APIs, logs, databases, files, streams)
        ↓
  ┌─────────────────────────────────────┐
  │         INGESTION LAYER             │
  │   (Fivetran, Airbyte, Kafka)        │
  └─────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────┐  ← Spark lives here
  │      PROCESSING / TRANSFORM LAYER   │
  │   (Apache Spark / PySpark)          │
  │   - Batch processing huge datasets  │
  │   - Stream processing (real-time)   │
  │   - ML at scale                     │
  └─────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────┐
  │         STORAGE LAYER               │
  │   (Snowflake, Delta Lake, S3,       │
  │    BigQuery, Databricks)            │
  └─────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────┐
  │     MODELING / SERVING LAYER        │
  │   (dbt, Power BI, Metabase)         │
  └─────────────────────────────────────┘
```

**Compared to what you already use:**

| Tool | What it does | Scale |
|---|---|---|
| **pandas** | Transform data in Python | Fits in one machine's RAM |
| **dbt** | Transform data using SQL inside a warehouse | Warehouse-scale |
| **Spark** | Transform data across a cluster of machines | Virtually unlimited |

The honest truth: **if your data fits in Snowflake and dbt handles it fine, you don't need Spark.** Spark shines when data is too big for a single machine, when you need real-time stream processing, or when you're doing ML at scale.

---

## 3. The Architecture — How Spark Actually Works

Imagine a company with a CEO and workers:

```
┌──────────────────────────────────────────────────────┐
│                    YOUR PROGRAM                       │
│              (the SparkSession object)                │
└──────────────────────────┬───────────────────────────┘
                           │ submits job
                           ↓
┌──────────────────────────────────────────────────────┐
│                  DRIVER (the CEO)                     │
│  - Understands your code                              │
│  - Creates an execution plan                          │
│  - Divides work into tasks                            │
│  - Coordinates everything                             │
└────────┬───────────────┬──────────────┬──────────────┘
         │               │              │  sends tasks
         ↓               ↓              ↓
    ┌─────────┐     ┌─────────┐    ┌─────────┐
    │Executor │     │Executor │    │Executor │  (the workers)
    │(Worker) │     │(Worker) │    │(Worker) │
    │ Node 1  │     │ Node 2  │    │ Node 3  │
    └─────────┘     └─────────┘    └─────────┘
```

- **Driver:** Your program. It plans the work.
- **Executors:** JVM processes on worker machines that actually run the computation.
- **Cluster Manager:** (YARN, Kubernetes, or Spark Standalone) — allocates resources. Think of it as HR.

---

## 4. The Most Fundamental Concept: Lazy Evaluation

This is the single most important thing to understand about Spark, and it confuses most beginners.

**In pandas, code executes immediately:**
```python
df = pd.read_csv("huge_file.csv")   # reads file RIGHT NOW
df2 = df[df["age"] > 25]           # filters RIGHT NOW
```

**In Spark, nothing executes until you explicitly ask for results:**
```python
df = spark.read.csv("huge_file.csv")   # builds a PLAN, reads nothing
df2 = df.filter(df["age"] > 25)        # adds to the PLAN, does nothing
df3 = df2.groupBy("country").count()   # still just a PLAN

df3.show()   # ← THIS is when Spark actually runs everything
```

This is called **lazy evaluation**, and it's genius because:
- Spark sees your *entire* plan before executing anything
- It can optimize it (reorder operations, skip unnecessary steps)
- It only reads the data it actually needs

**Transformations vs Actions** — this distinction flows directly from laziness:

```
Transformations (lazy — just build the plan):
  .filter()   .select()   .groupBy()   .join()   .withColumn()

Actions (trigger actual execution):
  .show()   .count()   .collect()   .write()   .save()
```

---

## 5. The Core Data Structure: DataFrame

You already know pandas DataFrames and SQL tables. Spark DataFrames are the same concept — rows and columns — but distributed across your cluster.

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("MyApp").getOrCreate()

# Read a massive CSV — Spark splits it across all workers automatically
df = spark.read.csv("s3://my-bucket/huge-dataset.csv", header=True)

# This looks just like SQL or pandas
result = (df
    .filter(df["country"] == "Hungary")
    .groupBy("product_category")
    .agg({"revenue": "sum"})
    .orderBy("sum(revenue)", ascending=False)
)

result.show(10)  # triggers execution
```

**You can also write pure SQL on Spark DataFrames:**
```python
df.createOrReplaceTempView("sales")

result = spark.sql("""
    SELECT product_category, SUM(revenue) as total_revenue
    FROM sales
    WHERE country = 'Hungary'
    GROUP BY product_category
    ORDER BY total_revenue DESC
""")
```

Given your SQL background, this is the fastest path in.

---

## 6. Partitions — How Spark Distributes Data

When Spark reads a 1TB file, it doesn't load it whole. It splits it into **partitions** — chunks — and sends each chunk to a different executor.

```
1TB file
    ↓ Spark splits into partitions
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Part 1 │ │ Part 2 │ │ Part 3 │ │ Part 4 │  ← 4 executors work in parallel
│ 250GB  │ │ 250GB  │ │ 250GB  │ │ 250GB  │
└────────┘ └────────┘ └────────┘ └────────┘
```

Most operations (filter, map, select) happen *within* each partition independently — perfect parallelism, no coordination needed.

Some operations (groupBy, join, orderBy) require data from *multiple* partitions to move around — this is called a **shuffle**, and it's the main performance cost in Spark jobs. Understanding when shuffles happen is what separates good Spark engineers from great ones.

---

## 7. The Conceptual Map

```
SPARK ECOSYSTEM
│
├── Spark Core          — the engine (scheduling, memory, I/O)
│
├── Spark SQL           — DataFrames + SQL queries  ← start here
│
├── Spark Streaming     — real-time data processing
│   (Structured Streaming)
│
├── MLlib               — machine learning at scale
│
└── GraphX              — graph processing (rare in practice)
```

---

## How to Start — A Concrete Path Given Your Background

**Week 1 — Environment + SQL API**
- Set up Databricks Community Edition (free)
- Read a CSV, run Spark SQL queries — leverage your SQL muscle memory
- Understand lazy eval: call `.explain()` on a DataFrame to see the plan

**Week 2 — DataFrame API + Transformations**
- Learn the DataFrame API: `filter`, `select`, `withColumn`, `groupBy`, `join`
- Understand the difference between narrow (no shuffle) and wide (shuffle) transformations

**Week 3 — Internals**
- Study partitioning and when shuffles happen
- Use the **Spark UI** (built-in web UI at port 4040) to visualize job execution — this is like EXPLAIN ANALYZE for Spark

**Week 4 — Real-world patterns**
- Reading/writing Parquet and Delta Lake files
- Window functions in Spark SQL 
- Connecting Spark to your existing stack concepts

dbt + Snowflake: The main shift is just moving from a warehouse doing the distributed work for you, to you being aware of *how* the distribution happens.



- I want to understand what these concepts are and how they are related: 

CLIENT
    DRIVER 
    SparkContext 

STANDALONE CLUSTER
    MASTER
    ClusterManager

    WORKER
    Executor
    Task | Task

Now let me explain each piece and why it exists.

---

## The Client

The **Client** is simply your machine — your laptop, a CI server, wherever you write and submit your Spark program. It's not doing any data processing. It's the entry point.

Inside the Client lives the **Driver** — the process that runs your actual Python/Scala code. When you write a PySpark script, that script *is* the Driver. It has two jobs: (1) define what needs to be done, and (2) coordinate who does it.

Inside the Driver lives the **SparkContext** — a single object, created at startup, that represents the connection to the cluster. Think of it as a phone line. Before SparkContext existed, the Driver had no way to talk to any cluster. It authenticates with the cluster, negotiates resources, and is the channel through which jobs are submitted. In modern Spark you mostly see `SparkSession` (a higher-level wrapper), but `SparkContext` lives inside it doing the same job.

```python
spark = SparkSession.builder.appName("MyApp").getOrCreate()
# spark.sparkContext is the SparkContext underneath
```

---

## The Standalone Cluster

"Standalone" just means Spark is managing its own cluster, without an external resource manager like Kubernetes or YARN. It has its own built-in Master/Worker system.

The **Master** is the cluster's brain. Its only job is resource management — it knows how many machines are available, how much memory/CPU each has, and it decides which Worker gets which job. It does *zero* data processing. It's equivalent to a scheduler. The term **ClusterManager** is the abstract role — "the thing that manages resources." In Standalone mode, the Master *is* the ClusterManager. In Kubernetes mode, Kubernetes plays this role instead.

The **Worker** is a physical machine (or VM) in the cluster. Workers register themselves with the Master on startup and say "I'm here, I have 16 cores and 64GB RAM." The Worker itself doesn't process data either — it's just a host.

---

## Executor & Task — where the actual work happens

When the Master assigns a job to a Worker, the Worker launches an **Executor** — a JVM process that boots up on that machine and stays alive for the duration of your application. The Executor is the actual engine: it holds data in memory (your partitions), runs computation, and reports results back to the Driver.

A **Task** is the smallest unit of work. The Driver takes your transformation plan, slices it into tasks (one per data partition), and sends them to Executors. An Executor runs multiple tasks concurrently — one per CPU core it's been allocated. So if an Executor has 4 cores, it runs 4 tasks at once, each processing its own chunk of data in parallel.

---

## The flow end to end

```
You write code on the Client
  → Driver starts, SparkContext connects to Master
    → Master finds available Workers, tells them to launch Executors
      → Driver sends Tasks to Executors
        → Executors run Tasks in parallel on their data partitions
          → Results flow back to the Driver
```

The key insight: the **Driver plans**, the **Master allocates**, the **Executors execute**. These are three completely separate concerns, and Spark separates them cleanly because at scale they need to run on different machines entirely.


- wait, why Driver sends Task to Executors? since Driver submits job to Master I thought its master's responsibility to send tasks to Executors

Really sharp catch — this trips up almost everyone, because the intuition says "Master is in charge, so Master must be doing the coordination." But the reality is more nuanced.

## The Master's job ends at resource allocation

Here's the precise split:

**Master's responsibility:** "Here are the Executors you can use. Their addresses are X, Y, Z. Done."

**Driver's responsibility:** Everything after that — planning the job, slicing it into tasks, sending tasks directly to Executors, monitoring progress, retrying failures, collecting results.

So the Master is more like **HR** than a manager. It hires the workers (launches Executors) and hands them over. After that it steps back completely. It doesn't know or care what tasks are being run.

---

## Why is it designed this way?

Because the **Driver already has all the information the Master doesn't.**

The Driver knows:
- The full execution plan (the DAG of transformations)
- Which partition lives on which Executor
- Which tasks failed and need retrying
- The data locality (send this task to the Executor that already has the data)

The Master knows none of this — it only knows resource availability. So it would make no sense to route task scheduling through the Master. That would just add latency and make the Master a bottleneck.

---

## The corrected flow

```
SparkContext → Master       "I need resources"
Master → Workers            "launch Executors"
Workers → Executors         Executors boot up
Executors → SparkContext    "I'm alive, here's my address"

--- Master's job is now done ---

Driver → Executors          sends Tasks directly
Executors → Driver          sends results/status directly
```

The Master is completely out of the loop once Executors are running. The Driver and Executors talk peer-to-peer from that point forward.

---

## A concrete analogy

Think of staffing an event:

- **Master** = staffing agency. You call them, they send you 10 workers and give you their phone numbers. Their job is done.
- **Driver** = event manager. You now call those 10 workers directly, assign them specific tasks, check their progress, and handle any issues.

The staffing agency doesn't coordinate the event — you do, directly with the workers.

This is also why when the **Driver crashes, the entire job dies** — the Master has no idea what tasks were running or what to do next. The Driver was the brain. The Master just provided the muscle.


- thanks
so only work of Master is to introduce Workers to the Driver and leave the game?

Yes, essentially. That's a great way to remember it.

Though to be precise — the Master doesn't even introduce *Workers* to the Driver. It introduces **Executors**. The Worker is just the physical machine. What the Driver actually gets is a list of running Executor processes (their host addresses and ports). The Worker itself is never in the conversation after that.

So the full Master lifecycle is:

1. Receives resource request from SparkContext ("I need 4 Executors with 8GB each")
2. Finds Workers with enough capacity
3. Tells those Workers to launch Executor processes
4. Tells the Driver "your Executors are running at these addresses"
5. **Exits the conversation entirely**

After step 4, the Master only does one thing: **monitors Worker heartbeats**. If a Worker machine dies, the Master tells the Driver "hey, that Executor is gone." But even then, it's the Driver that decides what to do about it (retry the tasks, request a replacement Executor, etc.).

So the Master has exactly two active moments — **at the start** (allocate resources) and **if something dies** (notify the Driver). Everything in between is the Driver's world.


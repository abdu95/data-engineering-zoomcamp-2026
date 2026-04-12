# import os
# os.environ["JAVA_HOME"] = r"C:\Java\jdk-21"
# os.environ["HADOOP_HOME"] = r"C:\hadoop"
# os.environ["PATH"] = r"C:\Java\jdk-21\bin;C:\hadoop\bin;" + os.environ["PATH"]

# # Monkey-patch Popen to print the command before running
# import subprocess
# original_popen = subprocess.Popen
# def debug_popen(cmd, **kwargs):
#     print("POPEN COMMAND:", cmd)
#     return original_popen(cmd, **kwargs)
# subprocess.Popen = debug_popen

# from pyspark.sql import SparkSession
# spark = SparkSession.builder \
#     .master("local[*]") \
#     .appName('test') \
#     .getOrCreate()


import pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("local[*]") \
    .appName('test') \
    .getOrCreate()

print(f"Spark version: {spark.version}")

# df = spark.range(10)
# df.show()

spark.stop()
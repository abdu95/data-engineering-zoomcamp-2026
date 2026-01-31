
01-docker-terraform 

- Terraform videos - 3
- set up GCP account

02-workflow-orchestration

- GCP video

1. as you can see, I am getting CSV file and inserting into database. 
I want to modify my flow: I want to create ctrl_row_count  table. these table will have columns: taxi_type (green or yellow), year, month, csv_row_count and table_row_count.  
csv_row_count should show how many rows in CSV before inserting to table. 
table_row_count should show how many rows in the final table after we insert data from staging table. table_row_count is tricky: it should show not total final table row count, but only for the insterted year, insterted month only. 
This way I can ensure that CSV file and final table row count match
2. can you also add LOAD_DT column to final table? It should show datetime when data was loaded to table
3. loading one file for about a minute is too long. How to optimize?
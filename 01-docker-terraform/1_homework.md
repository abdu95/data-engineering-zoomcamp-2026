# Data Engineering Zoomcamp 

## Homework 1: Docker, SQL and Terraform 

### Question 1. What's the version of pip in the python:3.13 image? (1 point)

- Get python image, enter the container and open bash
`docker run -it --rm python:3.13 bash`

- Check pip version inside the container
`pip --version`

**Answer**: 25.3 


### Question 2. Understanding Docker networking and docker-compose

Given the following docker-compose.yaml, what is the hostname and port that pgadmin should use to connect to the postgres database?


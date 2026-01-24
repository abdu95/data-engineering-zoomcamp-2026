
Docker for Data Engineering: Postgres, Docker Compose, and Real-World Workflows - Alexey Grigorev

Pipeline

pipeline folder + pipeline.py

`python pipeline.py 13`
run script with args 


`print("arguments", sys.argv)`
shows args that was passed while running the script 


## Using uv - Modern Python Package Manager

`uv` - a modern, fast Python package and project manager written in Rust. It's much faster than pip and handles virtual environments automatically.

`pip install uv`

Now initialize a Python project with uv:

`uv init --python=3.13`

This creates a pyproject.toml file for managing dependencies and a .python-version file.
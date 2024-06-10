# Use an NVIDIA CUDA base image that supports Ubuntu 22.04
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Python 3.8
RUN apt-get update && \
    apt-get install -y python3.8 python3-pip

# Optionally, install additional Python dependencies using requirements.txt
# COPY requirements.txt .
# RUN python3.8 -m pip install -r requirements.txt

# Command to run on container start, for example:
# CMD ["python3.8", "your_script.py"]

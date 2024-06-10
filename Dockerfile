# Use an NVIDIA CUDA base image that supports Ubuntu 22.04
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# Set the working directory in the container
WORKDIR /app

# Install software-properties-common to add new repository
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y software-properties-common

# Add the deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa

# Install Python 3.8
RUN apt-get update && \
    apt-get install -y python3.8 python3-pip

# Set Python 3.8 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# Set pip3 as the default for pip3, assuming pip3 is correctly installed
RUN update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1

# Copy the current directory contents into the container at /app
COPY . .

# Optionally, install additional Python dependencies using requirements.txt
# COPY requirements.txt .
# RUN python3.8 -m pip install -r requirements.txt

# Command to run on container start, for example:
# CMD ["python3.8", "your_script.py"]
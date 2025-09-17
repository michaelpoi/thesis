# Use the official Python 3.10 Alpine image
FROM python:3.10-slim

RUN apt-get update

RUN apt-get install -y libgl1

RUN apt-get install -y build-essential

RUN apt-get install -y libglib2.0-0

RUN pip install --upgrade pip wheel setuptools

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY metadrive /app/metadrive-main

RUN cd metadrive-main && \
    pip install -e .

RUN python -m metadrive.pull_asset

# Copy the rest of the application code
COPY . .

EXPOSE 8000
# Run the Python script
CMD ["python", "main.py"]
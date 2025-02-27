# Use a minimal Python base image
FROM python:3.10-slim

RUN apt-get update

RUN apt-get install -y libgl1-mesa-glx

RUN apt-get install -y build-essential

RUN apt-get install -y libglib2.0-0

# Set working directory
WORKDIR /app

COPY requirements.txt .

COPY metadrive-main /app/metadrive-main


RUN pip install --upgrade pip

RUN cd metadrive-main && \
    pip install -e .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# Set entrypoint
CMD ["python", "main.py"]

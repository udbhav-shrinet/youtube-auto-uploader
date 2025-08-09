# Start with an official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, including ffmpeg.
# The cleanup commands help keep the final image size smaller.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy your Python package requirements file
COPY requirements.txt .

# Install your Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Start the Functions Framework server. It will listen for requests
# and execute your function. The port is handled automatically by Google Cloud.
CMD ["functions-framework", "--target=pubsub_handler"]

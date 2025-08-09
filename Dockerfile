# Start with an official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

#
# Install a minimal, static build of ffmpeg instead of using apt-get
#
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl xz-utils && \
    \
    # Download the pre-compiled ffmpeg binary
    curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o ffmpeg.tar.xz && \
    \
    # Extract the package
    tar -xf ffmpeg.tar.xz && \
    \
    # Move the ffmpeg program to a location that's in the system's PATH
    mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /usr/local/bin/ && \
    \
    # Clean up all the temporary files and packages
    rm -rf ffmpeg.tar.xz ffmpeg-master-latest-linux64-gpl && \
    apt-get purge -y --auto-remove curl xz-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy your Python package requirements file
COPY requirements.txt .

# Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Command to run your function when the container starts
CMD ["functions-framework", "--target=pubsub_handler"]

# Use the official Python 3.10 Alpine image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies and Python build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libmariadb-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    
# Copy the application code to the working directory
COPY . .

# Set the command to run when the container starts
CMD ["python3", "consumer.py"]
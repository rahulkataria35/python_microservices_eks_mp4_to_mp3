FROM python:3.10-slim

# Set the working directory
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

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["python3", "main.py"]
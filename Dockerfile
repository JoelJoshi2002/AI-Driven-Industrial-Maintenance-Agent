# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (needed for MySQL/MariaDB clients)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Default command (will be overridden by docker-compose)
CMD ["python", "--version"]
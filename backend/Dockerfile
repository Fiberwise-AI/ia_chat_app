FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install setuptools/wheel for editable installs
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (excluding local packages)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code AND entrypoint script
COPY . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8091

# Use entrypoint script that installs local packages and starts server
ENTRYPOINT ["/app/docker-entrypoint.sh"]

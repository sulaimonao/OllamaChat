# Use a lightweight base image with Python and necessary tools
FROM python:3.11-slim

# Install any required system packages (e.g., build-essential for compiling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements.txt (create this)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Expose a port (optional, if you want to use network communication - but generally avoid it)
# EXPOSE 8888

# Set resource limits (adjust as needed)
# Example: Limit memory to 512MB
# RUN ulimit -m 524288

# You might set a non-root user here for improved security, but it adds complexity
# RUN useradd -m -s /bin/bash sandboxuser
# USER sandboxuser

# Command to run (you'll override this when starting the container)
CMD ["bash"]
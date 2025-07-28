# Use platform-compatible slim python image (for amd64)
FROM python:3.9-slim
WORKDIR /app


WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY src ./src

# Create input/output folders in the container
RUN mkdir -p /app/input /app/output

# Set entrypoint to main script
ENTRYPOINT ["python", "src/main.py"]

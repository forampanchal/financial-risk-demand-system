# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Create artifacts directory
RUN mkdir -p artifacts

# Default command (run daily batch)
CMD ["python", "-m", "src.pipeline.daily_pipeline"]
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Install gcloud CLI
RUN curl https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY setup.py .
COPY README.md .

# Install the application
RUN pip install -e .

# Create directories for reports and logs
RUN mkdir -p reports logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Create non-root user
RUN useradd -m -u 1000 optimizer && \
    chown -R optimizer:optimizer /app
USER optimizer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "src/main.py"]
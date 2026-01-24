FROM python:3.13.7-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env.example .env

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "src/main.py"]

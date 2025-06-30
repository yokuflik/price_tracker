# Use lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI default port
EXPOSE 8000

# Run FastAPI app (adjust "myFlightsApi:app" to your actual entrypoint)
CMD ["uvicorn", "myFlightsApi:app", "--host", "0.0.0.0", "--port", "8000"]

# Use the official Python base image with specific version
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade pip first
RUN pip install --upgrade pip

# Copy the requirements.txt first to leverage Docker cache if requirements don't change
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the app code to the working directory
COPY . .

# Expose port for Streamlit (default port is 8501)
EXPOSE 5000

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]

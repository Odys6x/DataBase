# Base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN pip install gunicorn
# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

RUN sed -i '/pywin32/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Add Rust for building certain dependencies
RUN apt-get update && apt-get install -y curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH"
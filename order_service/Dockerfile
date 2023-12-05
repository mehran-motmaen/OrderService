# Use the official Python base image
FROM python:3.9

# Set the maintainer label
LABEL maintainer="Merhan Motmaen <motmaen73@gmail.com>"

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE order_service.settings


# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8000
EXPOSE 8000


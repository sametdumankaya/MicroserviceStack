# Pull base image
FROM python:3.6

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy requirements file and install packages first
COPY requirements.txt /app/requirements.txt

# Set working directory
WORKDIR /app/

# Install required packages
RUN pip install -r /app/requirements.txt

# Copy files to image
COPY . /app/

# Start app
CMD ["python", "start_data_source.py"]
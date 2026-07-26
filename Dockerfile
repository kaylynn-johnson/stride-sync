# Pull base image
FROM python:3.14-slim-bookworm

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /usr/src/app

# Copy requirements txt
COPY requirements.txt /usr/src/app/

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy project
COPY . /usr/src/app/

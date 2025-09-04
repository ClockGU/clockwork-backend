# Use the official Python image as the base
FROM python:3.13-slim

# Set environment variables for Poetry
ENV POETRY_VERSION=1.7.0 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app  

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set the working directory
WORKDIR /app

# Copy only the dependency files first for efficient caching
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry (ensure api module is included)
RUN poetry install --no-dev

# Copy the application code
COPY . /app  

# Expose the port the api will run on
EXPOSE 8000

# Command to run the api
ENTRYPOINT ["./entrypoint.sh"]
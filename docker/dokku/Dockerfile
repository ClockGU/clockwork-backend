# Use the official Python image as the base
FROM python:3.13-slim

# Set environment variables for Poetry
ENV POETRY_VERSION=1.7.0 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app  \
    POETRY_HOME="/opt/poetry"
ENV PATH="$PATH:$POETRY_HOME/bin"

RUN groupadd app --gid 32767
RUN adduser --ingroup app --home /app --uid 32767 --disabled-password --gecos "" app

# Install Poetry
RUN apt update && apt install -y curl

RUN curl -sSL https://install.python-poetry.org  | python3 -
COPY pyproject.toml poetry.lock /
RUN poetry install

COPY --chown=app:app docker/dokku/* /app/
USER app
COPY --chown=app:app . /app
# Set the working directory
WORKDIR /app
RUN chmod +x entrypoint.sh

# Command to run the api
ENTRYPOINT ["./entrypoint.sh"]
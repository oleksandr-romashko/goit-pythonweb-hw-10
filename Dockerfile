# Use official base Python image (Alpine = small & fast)
FROM python:3.12-slim

# Space optimization: Prevent Python from writing .pyc files to disk (Python recompiles on-the-fly anyway)
# Prevents .pyc & __pycache__ from being generated (saves space)
ENV PYTHONDONTWRITEBYTECODE=1
# Logs show optimization: Ensure stdout/stderr is unbuffered (e.g. logs show up immediately)
# Ensures logs show up in real-time (great for Docker logs)
ENV PYTHONUNBUFFERED=1

# Set working directory for the app inside container
WORKDIR /app

# Set PYTHONPATH to ensure modules can be found
ENV PYTHONPATH="/app"

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy only dependency files first
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Now copy full project (except what is in .dockerignore)
COPY ./entrypoint.sh ./entrypoint.sh
COPY ./src ./src
COPY ./migrations ./migrations
COPY ./alembic.ini ./alembic.ini
COPY ./static ./static
COPY ./LICENSE ./LICENSE

# Space optimization: Clean up __pycache__
# Cleans up any bytecode just in case something generates it during copy or install
# Why do this if PYTHONDONTWRITEBYTECODE=1 is set?
# Sometimes tools or scripts (e.g. local dev environments, tests) may have generated
# .pyc files before we copied them into the container. This command ensures that 
# no stale bytecode files remain in the final image — just in case.
RUN find . -type d -name '__pycache__' -exec rm -rf {} +

# Start application
ENTRYPOINT ["./entrypoint.sh"]

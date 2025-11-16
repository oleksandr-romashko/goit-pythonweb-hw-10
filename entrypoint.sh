#!/bin/sh
set -e

echo "Starting API service..."

echo "1) ⚙️  Running Alembic DB migrations..."
if ! poetry run alembic upgrade head; then
    echo "❌ Alembic migration failed!"
    exit 1
fi
echo "✅ DB migrations applied successfully."

echo "2) ⚙️  Creating superuser (if needed)..."
if ! poetry run python -m src.seed.seed_init_superuser; then
    echo "❌ Failed to create superuser."
    exit 1
fi
echo "✅ Superuser setup complete."

echo "3) ⚙️  Starting FastAPI..."
exec poetry run python -m src.main

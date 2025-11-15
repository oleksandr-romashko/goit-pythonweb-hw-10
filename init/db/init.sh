#!/bin/sh
set -e

echo "[INIT] Running init.sh..."
# echo "[INIT] Using DB_NAME=${DB_NAME}, DB_ADMIN_USER=${DB_ADMIN_USER}, DB_APP_USER=${DB_APP_USER}"

# Render SQL with placeholders replaced
sed -e "s|\${DB_NAME}|$DB_NAME|g" \
    -e "s|\${DB_APP_USER}|$DB_APP_USER|g" \
    -e "s|\${DB_APP_USER_PASSWORD}|$DB_APP_USER_PASSWORD|g" \
    /docker-entrypoint-initdb.d/templates/init.template.sql > /tmp/init.sql

echo "[INIT] SQL template rendered to /tmp/init.sql"

# Execute it directly, now that the DB already exists thanks to POSTGRES_DB
# wait for Postgres to be ready before running psql commands.
# Potential race with psql waiting for server

# Wait for DB and 'postgres' role to exist
until psql -U "$DB_ADMIN_USER" -d "$DB_NAME" -c '\du' | grep -q "$DB_ADMIN_USER"; do
  echo "[INIT] Waiting for role $DB_ADMIN_USER to exist..."
  sleep 1
done

# Execute it directly, now that the DB already exists thanks to POSTGRES_DB
psql -v ON_ERROR_STOP=1 --username "$DB_ADMIN_USER" --dbname "$DB_NAME" -f /tmp/init.sql

echo "[INIT] SQL init script executed successfully."

# Clean up
rm -f /tmp/init.sql
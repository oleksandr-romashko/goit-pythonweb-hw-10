#!/bin/sh
set -e

echo "[PGADMIN INIT] Starting pgAdmin to initialize DB..."
/entrypoint.sh &

echo "[PGADMIN INIT] Waiting for pgAdmin database to be initialized..."
while [ ! -f "/var/lib/pgadmin/pgadmin4.db" ]; do
  sleep 1
done

echo "[PGADMIN INIT] Rendering servers.json from template..."
sed \
  -e "s|\${DB_HOST}|${DB_HOST}|g" \
  -e "s|\${DB_ADMIN_USER}|${DB_ADMIN_USER}|g" \
  -e "s|\${DB_NAME}|${DB_NAME}|g" \
  /pgadmin4/servers.template.json > /pgadmin4/servers.json

# Optional: debug copy
cp /pgadmin4/servers.json /var/lib/pgadmin/debug_servers.json

echo "[PGADMIN INIT] Done. Letting pgAdmin finish startup."
wait
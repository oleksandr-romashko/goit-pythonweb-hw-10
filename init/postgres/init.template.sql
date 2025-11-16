-- Create app user if not exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_APP_USER}'
  ) THEN
    RAISE NOTICE 'Creating app user...';
    CREATE USER ${DB_APP_USER} WITH PASSWORD '${DB_APP_USER_PASSWORD}';
  ELSE
    RAISE NOTICE 'User ${DB_APP_USER} already exists, skipping creation.';
  END IF;
END
$$;

-- Grant access to main DB
DO $$ BEGIN RAISE NOTICE 'Granting DB access to user...'; END $$;
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_APP_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_APP_USER};

-- Grant privileges on schema public
DO $$ BEGIN RAISE NOTICE 'Granting privileges on schema public...'; END $$;
ALTER SCHEMA public OWNER TO ${DB_APP_USER};
GRANT ALL ON SCHEMA public TO ${DB_APP_USER};

-- Grant DML rights for existing tables/sequences
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${DB_APP_USER};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${DB_APP_USER};

-- Default privileges for future tables/sequences
DO $$ BEGIN RAISE NOTICE 'Granting default privileges for future tables/sequences...'; END $$;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${DB_APP_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO ${DB_APP_USER};

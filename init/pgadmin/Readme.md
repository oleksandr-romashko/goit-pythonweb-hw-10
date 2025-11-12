# How pgAdmin Initialization Works

This directory contains the initialization logic for the `pgAdmin` container in our Docker Compose setup.

## 🧠 Why this exists

We want to:

* Automatically configure pgAdmin with a connection to our **local PostgreSQL container**.
* Avoid manual server setup every time the container is started - server should be already there in the list of available servers.
* Ensure smoother onboarding for developers and better reproducibility.

## ⚙️ How it works (step-by-step)

1. Docker Compose mounts config files and templates
    In [compose.yaml](/compose.yaml), we mount our init folder into the pgAdmin container:

    ```yaml
    services:
        db-admin-panel::
            volumes:
                ...
    ```

    This mounts:
    * A custom shell script (*[pgadmin_custom_entrypoint.sh](./pgadmin_custom_entrypoint.sh) file*) that copies and applies the server config (done once at fist pgAdmin start). It substitute environment variables from `.env` file into servers data template and creates `servers.json` file that may be used by pgAdmin.
    * Template for servers list file (*[servers.template.json](./servers.template.json) file*) containing the connection details and information about servers.
        Some variables here are placeholders for real data to substitute.
    * Generated servers list (*`servers.json` file*) to be updated with actual servers data.
        Opt out from version control as content is been generated at initialization.
        Mounted ho view the file and have access to change it.
2. [servers.template.json](./servers.template.json) contains server connection config.
    This configuration tells pgAdmin to connect to the database service under its Docker hostname, using the postgres user.
3. [pgadmin_custom_entrypoint.sh](./pgadmin_custom_entrypoint.sh) injects the config on container start.
    This script is automatically executed when the pgAdmin container starts for the first time.
    It copies the [servers.template.json](./servers.template.json) file content into the pgAdmin servers file (`servers.json`) with substituted selected variables from `.env` file.. That makes pgAdmin load the server connection config on the first run.

## 📁 Files Overview
| File                           | Purpose                                                                                                                                              |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pgadmin_custom_entrypoint.sh` | Custom entrypoint script that injects servers.template.json into pgAdmin's data directory as `servers.json` with substituted environmental variables |
| `servers.template.json`        | JSON template containing pgAdmin server connection config with placeholders for environmental variables                                              |

> ⚠️ Notes
> The connection is to the internal Docker hostname resolves via Docker's internal DNS.
> This setup will not re-apply servers.template.json if pgAdmin has already initialized — the data volume keeps it.

To reset/reload config:
```bash
docker-compose down -v
```

## 🧪 Example Use Case

When you open pgAdmin [localhost:5050](http://localhost:5050) (port may vary based on your settings in `.env`), it will already contain a pre-configured server. Values by default are (actual settings may vary based on your settings in `.env`):
```
Host: ${DB_HOST}
MaintenanceDB: ${DB_NAME}
Username: ${DB_ADMIN_USER}
```

No manual setup required. Just log in with the email/password you provided via environment variables.
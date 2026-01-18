# Nextcloud Full Suite (Docker Compose + MariaDB)

A secure, reproducible, and production-ready deployment of **Nextcloud** backed by **MariaDB** using Docker Compose.

## Features

- Docker Compose v2 compatible
- Secrets stored in `.env` (not committed)
- Named volumes for persistence
- Explicit networks and restart policies
- Health-aware database dependency

## Architecture

```
┌────────────┐        ┌──────────────┐
│   Client   │ ───▶   │  Nextcloud   │
│  (Browser) │        │  App Server  │
└────────────┘        └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   MariaDB    │
                      │  Database    │
                      └──────────────┘
```

- **Nextcloud**: Application container (LinuxServer image)
- **MariaDB**: Persistent SQL database
- **Bridge network**: Isolated internal communication
- **Named volumes**: Database + Nextcloud data persistence

## Prerequisites

- Ubuntu Server 24.04 LTS (or similar)
- Docker Engine + Docker Compose v2

### Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Log out and back in for group changes to take effect.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/BalbyyO/HomeLab.git
cd HomeLab/nextcloud-guide
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Update the following values with **strong, unique passwords** (minimum 20 characters):

| Variable | Description |
|----------|-------------|
| `PUID` | User ID for file permissions (run `id -u`) |
| `PGID` | Group ID for file permissions (run `id -g`) |
| `TZ` | Your timezone (e.g., `America/New_York`) |
| `MYSQL_ROOT_PASSWORD` | MariaDB root password |
| `MYSQL_PASSWORD` | Nextcloud database user password |

### 3. Deploy

```bash
docker compose up -d
```

### 4. Access Nextcloud

Open your browser:

```
https://<your-server-ip>
```

Complete the web installer using:

| Field | Value |
|-------|-------|
| Database host | `mariadb` |
| Database user | Value from `.env` (`MYSQL_USER`) |
| Database password | Value from `.env` (`MYSQL_PASSWORD`) |
| Database name | `nextcloud` |

## File Structure

```
nextcloud-guide/
├── docker-compose.yml   # Container definitions
├── .env.example         # Template for environment variables
├── .gitignore           # Excludes .env from version control
└── README.md            # This file
```

## Security Best Practices

- Secrets stored in `.env` file (never committed)
- No plaintext passwords in docker-compose.yml
- Non-root containers (LinuxServer images)
- Isolated Docker network
- Health-based startup order ensures database is ready

## Maintenance

### View Logs

```bash
docker compose logs -f
docker compose logs -f nextcloud
docker compose logs -f mariadb
```

### Update Containers

```bash
docker compose pull
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### Backup Volumes

```bash
# Backup MariaDB data
docker run --rm \
  -v nextcloud-guide_mariadb_data:/volume \
  -v $(pwd):/backup \
  alpine tar czf /backup/mariadb-backup.tar.gz -C /volume .

# Backup Nextcloud config
docker run --rm \
  -v nextcloud-guide_nextcloud_config:/volume \
  -v $(pwd):/backup \
  alpine tar czf /backup/nextcloud-config-backup.tar.gz -C /volume .

# Backup Nextcloud data
docker run --rm \
  -v nextcloud-guide_nextcloud_data:/volume \
  -v $(pwd):/backup \
  alpine tar czf /backup/nextcloud-data-backup.tar.gz -C /volume .
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Database connection fails | Verify `.env` values match between services |
| Permission errors | Ensure `PUID`/`PGID` match your host user (`id -u` / `id -g`) |
| Container won't start | Check logs: `docker compose logs mariadb` |
| Slow performance | Consider adding Redis (see improvements below) |
| HTTPS certificate warnings | Configure a reverse proxy with Let's Encrypt |

## Optional Improvements

- **Redis**: Add file locking and caching for better performance
- **Reverse Proxy**: Use Traefik or Nginx Proxy Manager for SSL termination
- **Cron Container**: Enable background jobs for Nextcloud
- **Docker Secrets**: Replace `.env` with Docker secrets for enhanced security
- **Fail2ban**: Add brute-force protection

## License

MIT License - See [LICENSE](../LICENSE) for details.

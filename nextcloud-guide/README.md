# Nextcloud Production Stack

Production-ready Docker Compose deployment for Nextcloud with MariaDB, Redis, and automated background jobs.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Bridge Network                    │
│                      (nextcloud_net)                        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   MariaDB   │  │    Redis    │  │      Nextcloud      │  │
│  │   (11.4)    │  │  (7-alpine) │  │   (LinuxServer.io)  │  │ 
│  │             │  │             │  │                     │  │
│  │  Database   │  │ File Lock   │  │    Web Interface    │  │
│  │  Storage    │  │   Cache     │  │       :443          │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │             │
│         └────────────────┴────────────────────┘             │
│                          │                                  │
│                   ┌──────┴──────┐                           │
│                   │    Cron     │                           │
│                   │  (5 min)    │                           │
│                   │ Background  │                           │
│                   │    Jobs     │                           │
│                   └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Image | Purpose |
|---------|-------|---------|
| **nextcloud** | `lscr.io/linuxserver/nextcloud:29.0.10` | Main Nextcloud application server |
| **mariadb** | `mariadb:11.4` | Database backend with Nextcloud-optimized settings |
| **redis** | `redis:7-alpine` | Transactional file locking and memory cache |
| **cron** | `lscr.io/linuxserver/nextcloud:29.0.10` | Background job execution every 5 minutes |

### Service Details

**MariaDB**
- Configured with `READ-COMMITTED` transaction isolation and `ROW` binlog format (Nextcloud requirements)
- Persistent volume for data durability
- Health check ensures database is ready before Nextcloud starts

**Redis**
- Used for transactional file locking (prevents conflicts during simultaneous edits)
- Memory-only configuration (no persistence) - acts as pure cache
- Limited to 128MB with LRU eviction policy
- Internal network only - not exposed to host

**Cron**
- Runs `cron.php` every 5 minutes
- Shares volumes with main Nextcloud container
- Handles background tasks: file scanning, cleanup, notifications, etc.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PUID` | User ID for file ownership | `1000` | Yes |
| `PGID` | Group ID for file ownership | `1000` | Yes |
| `TZ` | Timezone | `UTC` | Yes |
| `MYSQL_ROOT_PASSWORD` | MariaDB root password | - | Yes |
| `MYSQL_DATABASE` | Database name | `nextcloud` | Yes |
| `MYSQL_USER` | Database user | `nextcloud` | Yes |
| `MYSQL_PASSWORD` | Database user password | - | Yes |
| `NEXTCLOUD_PORT` | HTTPS port | `443` | No |

## Deployment

### Prerequisites

- Ubuntu Server 24.04 LTS
- Docker Engine 24.0+
- Docker Compose v2.20+

### Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url> nextcloud-docker
   cd nextcloud-docker
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   ```

3. **Generate secure passwords**

   ```bash
   # Generate and set passwords
   echo "MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)" >> .env.generated
   echo "MYSQL_PASSWORD=$(openssl rand -base64 32)" >> .env.generated

   # Review and copy to .env
   cat .env.generated
   ```

4. **Configure environment variables**

   Edit `.env` with your settings:
   ```bash
   nano .env
   ```

   Set your user/group IDs:
   ```bash
   # Find your IDs
   id -u  # PUID
   id -g  # PGID
   ```

5. **Validate configuration**

   ```bash
   docker compose config
   ```

6. **Start the stack**

   ```bash
   docker compose up -d
   ```

7. **Monitor startup**

   ```bash
   docker compose logs -f
   ```

8. **Access Nextcloud**

   Open `https://your-server-ip` in your browser.

### Post-Installation

1. **Complete web setup** - Create admin account through the web interface

2. **Verify Redis is working**

   ```bash
   docker exec -it nextcloud-redis redis-cli ping
   # Should return: PONG
   ```

3. **Verify cron is running**

   ```bash
   docker logs nextcloud-cron
   ```

4. **Set cron as background job method**

   In Nextcloud Admin → Basic settings → Background jobs, select "Cron"

## Security Notes

### Implemented Security Measures

- **No hardcoded secrets** - All credentials via environment variables
- **Internal Redis** - Not exposed outside Docker network
- **Health checks** - Services wait for dependencies
- **Explicit image tags** - No `latest` tags for reproducibility
- **Non-root execution** - LinuxServer images run as specified PUID/PGID

### Recommended Additional Security

1. **Reverse Proxy with SSL**

   Place behind a reverse proxy (Traefik, Caddy, nginx) for:
   - Valid SSL certificates (Let's Encrypt)
   - Rate limiting
   - Additional headers

2. **Firewall Configuration**

   ```bash
   # Allow only HTTPS
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **Regular Updates**

   ```bash
   # Check for image updates
   docker compose pull
   docker compose up -d
   ```

4. **Backup Strategy**

   - Database: Regular mysqldump exports
   - Data: Backup `nextcloud_data` volume
   - Config: Backup `nextcloud_config` volume

## Maintenance

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nextcloud
docker compose logs -f mariadb
docker compose logs -f cron
```

### Updating Nextcloud

1. **Backup first**

   ```bash
   # Database backup
   docker exec nextcloud-mariadb mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" nextcloud > backup.sql
   ```

2. **Pull new images**

   ```bash
   docker compose pull
   ```

3. **Recreate containers**

   ```bash
   docker compose up -d
   ```

4. **Run upgrade (if needed)**

   ```bash
   docker exec -it nextcloud occ upgrade
   ```

### Database Maintenance

```bash
# Access MariaDB CLI
docker exec -it nextcloud-mariadb mysql -u root -p

# Optimize tables
docker exec nextcloud-mariadb mysqlcheck -u root -p"$MYSQL_ROOT_PASSWORD" --optimize nextcloud
```

### Nextcloud OCC Commands

```bash
# Run occ commands
docker exec -it nextcloud occ <command>

# Examples
docker exec -it nextcloud occ status
docker exec -it nextcloud occ maintenance:mode --on
docker exec -it nextcloud occ files:scan --all
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs <service-name>

# Check health status
docker compose ps
```

### Database connection errors

1. Verify MariaDB is healthy: `docker compose ps mariadb`
2. Check credentials in `.env` match
3. Ensure MariaDB data volume is accessible

### Redis connection issues

```bash
# Test Redis connectivity
docker exec -it nextcloud-redis redis-cli ping

# Check Redis logs
docker compose logs redis
```

### Cron not running

1. Check cron container logs: `docker compose logs cron`
2. Verify in Nextcloud Admin that "Cron" is selected as background job method
3. Check last cron execution time in Admin overview

### Permission issues

```bash
# Verify PUID/PGID match your user
id -u
id -g

# Check volume permissions
docker exec -it nextcloud ls -la /config
docker exec -it nextcloud ls -la /data
```

### Reset installation

```bash
# Stop and remove everything (DATA LOSS!)
docker compose down -v

# Start fresh
docker compose up -d
```

## Volumes

| Volume | Mount Point | Description |
|--------|-------------|-------------|
| `mariadb_data` | `/var/lib/mysql` | Database files |
| `nextcloud_config` | `/config` | Nextcloud configuration and www files |
| `nextcloud_data` | `/data` | User files and data |

### Backup Volumes

```bash
# List volumes
docker volume ls | grep nextcloud

# Backup a volume
docker run --rm -v nextcloud_data:/source -v $(pwd):/backup alpine tar czf /backup/nextcloud_data.tar.gz -C /source .
```

## License

This Docker Compose configuration is provided as-is for educational and production use.

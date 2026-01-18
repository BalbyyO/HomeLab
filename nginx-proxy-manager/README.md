# NGINX Proxy Manager with CrowdSec (Ubuntu 24.04)

A secure reverse proxy setup with NGINX Proxy Manager running in Docker and CrowdSec installed on the host for intrusion detection and prevention.

## Architecture

```
Internet
   │
   ▼
NGINX Proxy Manager (Docker)
   │
   ▼
Upstream Services

CrowdSec (host)
 ├─ Parses NGINX logs
 ├─ Local API on :9090
 └─ Blocks via NGINX bouncer
```

### Why This Design?

- Avoids Docker-inside-Docker complexity
- CrowdSec has full host visibility
- Easier firewall integration and future bouncer expansion
- Clean separation of concerns

## Prerequisites

- Ubuntu Server 24.04 LTS
- Root or sudo access
- Domain name (optional, for SSL certificates)
- Cloudflare account (optional, for DDNS)

## 1. VM Preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl ca-certificates gnupg
```

## 2. Install Docker Engine + Compose v2

```bash
curl -fsSL https://get.docker.com/ -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

Verify installation:

```bash
docker version
docker compose version
```

## 3. Directory Setup

```bash
sudo mkdir -p /docker/nginx-proxy-manager
cd /docker/nginx-proxy-manager
```

## 4. Configuration Files

Copy the example files from this repository:

```bash
# Copy docker-compose.yml and .env.example to /docker/nginx-proxy-manager
cp .env.example .env
```

Edit `.env` with your values:

```bash
nano .env
```

## 5. Deploy NGINX Proxy Manager

```bash
cd /docker/nginx-proxy-manager
docker compose up -d
docker ps
```

Access the admin UI:

```
http://<VM-IP>:81
```

Default credentials:
- Email: `admin@example.com`
- Password: `changeme`

**Change these immediately after first login.**

## 6. Install CrowdSec on the Host

```bash
curl -fsSL https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh | sudo bash
sudo apt install -y crowdsec crowdsec-nginx
```

Verify:

```bash
sudo systemctl status crowdsec
```

## 7. Configure CrowdSec to Listen on Port 9090

Edit the configuration:

```bash
sudo nano /etc/crowdsec/config.yaml
sudo nano /etc/crowdsec/local_api_credentials.yaml
```

Find the `api.server` section and set:

```yaml
api:
  server:
    listen_uri: 127.0.0.1:9090
```

Restart CrowdSec:

```bash
sudo systemctl restart crowdsec
```

Verify the port:

```bash
ss -tulpn | grep 9090
```

## 8. Link NGINX Proxy Manager Logs to CrowdSec

NPM stores logs inside its Docker volume. Create a symlink for CrowdSec:

```bash
sudo ln -s /var/lib/docker/volumes/nginx-proxy-manager_npm_data/_data/logs /var/log/nginx
```

Restart CrowdSec to pick up the logs:

```bash
sudo systemctl restart crowdsec
```

Check metrics:

```bash
sudo cscli metrics
```

## 9. Install NGINX Bouncer

Install the bouncer:

```bash
sudo apt install -y crowdsec-nginx-bouncer
```

Generate an API key:

```bash
sudo cscli bouncers add nginx-proxy-manager
```

Configure the bouncer:

```bash
sudo nano /etc/crowdsec/bouncers/crowdsec-nginx-bouncer.conf
```

Set:

```conf
API_URL=http://127.0.0.1:9090
API_KEY=<PASTE_KEY_FROM_PREVIOUS_STEP>
```

Restart NGINX:

```bash
sudo systemctl restart nginx
```

## 10. Validation

Check that everything is working:

```bash
# View active decisions (bans)
sudo cscli decisions list

# View recent alerts
sudo cscli alerts list

# Check NGINX Proxy Manager logs
docker logs nginx-proxy-manager

# Check CrowdSec metrics
sudo cscli metrics
```

## File Structure

```
/docker/nginx-proxy-manager/
├── docker-compose.yml
├── .env
└── .gitignore

/etc/crowdsec/
├── config.yaml
└── bouncers/
    └── crowdsec-nginx-bouncer.conf
```

## Exposed Ports

| Port | Service | Purpose |
|------|---------|---------|
| 80 | NGINX Proxy Manager | HTTP traffic |
| 443 | NGINX Proxy Manager | HTTPS traffic |
| 81 | NGINX Proxy Manager | Admin UI |
| 9090 | CrowdSec (localhost only) | Local API for bouncers |

## Security Notes

- The CrowdSec API only listens on localhost (127.0.0.1)
- Keep your `.env` file secure and never commit it to version control
- Regularly update container images and CrowdSec
- Consider adding the Cloudflare bouncer for edge protection

## Troubleshooting

### CrowdSec not seeing logs

1. Verify the symlink exists:
   ```bash
   ls -la /var/log/nginx
   ```

2. Check log file permissions:
   ```bash
   sudo ls -la /var/lib/docker/volumes/nginx-proxy-manager_npm_data/_data/logs/
   ```

3. Verify CrowdSec acquisition config:
   ```bash
   sudo cscli parsers list
   ```

### Bouncer not connecting

1. Verify the API is running:
   ```bash
   curl http://127.0.0.1:9090/health
   ```

2. Check bouncer registration:
   ```bash
   sudo cscli bouncers list
   ```

## Next Steps

- Add [CrowdSec Cloud Console](https://app.crowdsec.net/) for centralized monitoring
- Install iptables/nftables bouncer for firewall-level blocking
- Configure Cloudflare bouncer for edge protection
- Set up SSL certificates in NGINX Proxy Manager

## License

MIT

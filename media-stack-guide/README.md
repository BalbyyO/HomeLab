# Media Stack - Complete HomeLab Media Automation

A beginner-friendly Docker Compose stack for automating your media library. This stack includes everything you need to automatically download, organize, and stream movies and TV shows.

## What's Included

| Service | Port | Description |
|---------|------|-------------|
| **Jellyfin** | 8096 | Media server - stream to any device |
| **Jellyseerr** | 5055 | Request portal - users can request content |
| **Radarr** | 7878 | Movie automation - finds and downloads movies |
| **Sonarr** | 8989 | TV automation - finds and downloads TV shows |
| **Prowlarr** | 9696 | Indexer manager - connects to torrent/usenet indexers |
| **Bazarr** | 6767 | Subtitle automation - downloads subtitles |
| **qBittorrent** | 8080 | Download client - handles torrent downloads |
| **Gluetun** | - | VPN container - keeps your IP private |
| **FlareSolverr** | 8191 | Cloudflare bypass - helps indexers work |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Network                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Jellyfin │    │Jellyseerr│    │  Radarr  │    │  Sonarr  │  │
│  │  :8096   │    │  :5055   │    │  :7878   │    │  :8989   │  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │               │               │               │         │
│       └───────────────┴───────┬───────┴───────────────┘         │
│                               │                                  │
│                        ┌──────┴──────┐                          │
│                        │   /data     │ (Shared Storage)         │
│                        └──────┬──────┘                          │
│                               │                                  │
│  ┌──────────┐    ┌──────────┐│    ┌──────────┐    ┌──────────┐ │
│  │ Prowlarr │    │  Bazarr  ││    │FlareSolvr│    │  Gluetun │ │
│  │  :9696   │    │  :6767   ││    │  :8191   │    │   (VPN)  │ │
│  └──────────┘    └──────────┘│    └──────────┘    └────┬─────┘ │
│                              │                         │        │
│                              │                   ┌─────┴──────┐ │
│                              │                   │qBittorrent │ │
│                              │                   │   :8080    │ │
│                              └───────────────────┴────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Requirements

- **Operating System**: Ubuntu 22.04+ (or any Linux with Docker support)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **VPN Subscription**: Required for safe torrenting (PIA, Mullvad, NordVPN, etc.)
- **Storage**: Enough space for your media library

## Quick Start

### Step 1: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose-plugin

# Start Docker and enable on boot
sudo systemctl enable --now docker

# Add yourself to docker group (logout and back in after this)
sudo usermod -aG docker $USER
```

### Step 2: Create Directory Structure

```bash
# Create the data directory structure
sudo mkdir -p /data/{torrents,media}/{movies,tv}
sudo mkdir -p /data/torrents/{downloading,completed}

# Set ownership to your user (replace 1000:1000 with your PUID:PGID)
sudo chown -R 1000:1000 /data
```

Your directory structure should look like this:

```
/data/
├── torrents/
│   ├── downloading/    # Active downloads
│   ├── completed/      # Finished downloads
│   ├── movies/         # Movie torrents
│   └── tv/             # TV show torrents
└── media/
    ├── movies/         # Organized movie library
    └── tv/             # Organized TV library
```

### Step 3: Clone This Repository

```bash
# Clone the repo
git clone https://github.com/BalbyyO/media-stack-guide.git
cd media-stack-guide

# Create your .env file from the template
cp .env.example .env
```

### Step 4: Configure Your Environment

Edit the `.env` file with your settings:

```bash
nano .env
```

**Important settings to change:**

1. **PUID/PGID** - Find your values by running `id` in terminal
2. **TZ** - Your timezone (e.g., `America/New_York`, `Europe/London`)
3. **DATA_PATH** - Path to your data directory (default: `/data`)
4. **VPN credentials** - Your VPN username and password
5. **JELLYFIN_URL** - Your server's IP address

### Step 5: Start the Stack

```bash
# Pull the latest images
docker compose pull

# Start all containers
docker compose up -d

# Check status
docker compose ps
```

### Step 6: Access the Services

Open your browser and navigate to:

| Service | URL |
|---------|-----|
| Jellyfin | `http://YOUR_IP:8096` |
| Jellyseerr | `http://YOUR_IP:5055` |
| Radarr | `http://YOUR_IP:7878` |
| Sonarr | `http://YOUR_IP:8989` |
| Prowlarr | `http://YOUR_IP:9696` |
| Bazarr | `http://YOUR_IP:6767` |
| qBittorrent | `http://YOUR_IP:8080` |

Replace `YOUR_IP` with your server's IP address.

## Initial Configuration

### 1. qBittorrent Setup

1. Go to `http://YOUR_IP:8080`
2. Default login: `admin` / check logs for temporary password:
   ```bash
   docker compose logs qbittorrent | grep password
   ```
3. Go to **Settings > Downloads**
4. Set **Default Save Path** to `/data/torrents/completed`
5. Set **Keep incomplete torrents in** to `/data/torrents/downloading`

### 2. Prowlarr Setup (Indexers)

1. Go to `http://YOUR_IP:9696`
2. Go to **Settings > General** and note your API key
3. Go to **Indexers > Add Indexer**
4. Add your preferred indexers (torrent sites)
5. For Cloudflare-protected sites, add FlareSolverr:
   - Go to **Settings > Indexers > Add (FlareSolverr)**
   - Host: `http://flaresolverr:8191`

### 3. Radarr Setup (Movies)

1. Go to `http://YOUR_IP:7878`
2. Go to **Settings > Media Management**
   - Add root folder: `/data/media/movies`
3. Go to **Settings > Download Clients > Add**
   - Select qBittorrent
   - Host: `gluetun` (not localhost!)
   - Port: `8080`
4. Go to **Settings > General** and copy API key for Prowlarr

### 4. Sonarr Setup (TV Shows)

1. Go to `http://YOUR_IP:8989`
2. Go to **Settings > Media Management**
   - Add root folder: `/data/media/tv`
3. Go to **Settings > Download Clients > Add**
   - Select qBittorrent
   - Host: `gluetun`
   - Port: `8080`
4. Copy API key for Prowlarr

### 5. Connect Prowlarr to Radarr/Sonarr

1. In Prowlarr, go to **Settings > Apps**
2. Add Radarr:
   - Prowlarr Server: `http://prowlarr:9696`
   - Radarr Server: `http://radarr:7878`
   - API Key: (from Radarr settings)
3. Add Sonarr:
   - Prowlarr Server: `http://prowlarr:9696`
   - Sonarr Server: `http://sonarr:8989`
   - API Key: (from Sonarr settings)

### 6. Jellyfin Setup

1. Go to `http://YOUR_IP:8096`
2. Follow the setup wizard
3. Add media libraries:
   - Movies: `/data/media/movies`
   - TV Shows: `/data/media/tv`

### 7. Jellyseerr Setup

1. Go to `http://YOUR_IP:5055`
2. Sign in with Jellyfin
3. Connect to Radarr and Sonarr using their API keys

### 8. Bazarr Setup (Subtitles)

1. Go to `http://YOUR_IP:6767`
2. Go to **Settings > Sonarr/Radarr** and connect using API keys
3. Go to **Settings > Providers** and add subtitle providers
4. Go to **Settings > Languages** and configure your preferences

## Useful Commands

```bash
# View logs for all containers
docker compose logs -f

# View logs for specific container
docker compose logs -f radarr

# Restart all containers
docker compose restart

# Restart specific container
docker compose restart radarr

# Stop all containers
docker compose down

# Update all containers
docker compose pull && docker compose up -d

# Check VPN is working (should show VPN IP, not your real IP)
docker exec gluetun wget -qO- https://ipinfo.io

# View container resource usage
docker stats
```

## Troubleshooting

### VPN Not Connecting

```bash
# Check gluetun logs
docker compose logs gluetun

# Common fixes:
# 1. Verify VPN credentials in .env
# 2. Try different server regions
# 3. Check if your VPN provider is supported
```

### Permission Denied Errors

```bash
# Fix ownership of data directory
sudo chown -R 1000:1000 /data

# Verify your PUID/PGID
id
# Use these values in your .env file
```

### Container Won't Start

```bash
# Check what's wrong
docker compose logs <container_name>

# Recreate the container
docker compose up -d --force-recreate <container_name>
```

### qBittorrent WebUI Not Accessible

The qBittorrent WebUI runs through the VPN. If you can't access it:

1. Check if Gluetun is healthy: `docker compose ps`
2. Check Gluetun logs: `docker compose logs gluetun`
3. Make sure port 8080 is mapped in Gluetun, not qBittorrent

### Services Can't Connect to Each Other

Use container names (not `localhost`) when connecting services:
- qBittorrent host: `gluetun`
- Radarr host: `radarr`
- Sonarr host: `sonarr`
- Prowlarr host: `prowlarr`

## Hardware Acceleration (Optional)

The Jellyfin container includes Intel iGPU hardware acceleration by default. If you don't have an Intel iGPU, remove these lines from `compose.yaml`:

```yaml
devices:
  - /dev/dri:/dev/dri
```

For NVIDIA GPUs, see the [Jellyfin documentation](https://jellyfin.org/docs/general/administration/hardware-acceleration/).

## Security Notes

- **Never expose these services directly to the internet** without proper security (reverse proxy with authentication)
- Keep your `.env` file secure and never commit it to git
- Regularly update your containers: `docker compose pull && docker compose up -d`
- The VPN ensures your torrenting activity is private

## Support

- [Jellyfin Documentation](https://jellyfin.org/docs/)
- [Servarr Wiki](https://wiki.servarr.com/) (Radarr, Sonarr, Prowlarr, Bazarr)
- [Gluetun Wiki](https://github.com/qdm12/gluetun-wiki)
- [LinuxServer.io](https://docs.linuxserver.io/)

## License

MIT License - Feel free to use and modify as needed.

#!/bin/bash
# =============================================================================
# NormCode Server Deployment Script
# =============================================================================
#
# Automates the full deployment process on Ubuntu/Linux:
#   1. System dependencies check
#   2. Virtual environment setup
#   3. Python dependency installation
#   4. Configuration validation
#   5. Nginx configuration
#   6. Systemd service setup
#   7. Log rotation setup
#   8. Health check verification
#
# Usage:
#   ./deploy.sh                      # Full interactive deployment
#   ./deploy.sh --install-dir /opt/normcode    # Custom install directory
#   ./deploy.sh --skip-nginx         # Skip Nginx setup
#   ./deploy.sh --skip-systemd       # Skip systemd service setup
#   ./deploy.sh --update             # Update existing installation (skip setup)
#   ./deploy.sh --uninstall          # Remove service and configs
#
# =============================================================================

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Detect if running from deploy/ inside scripts/ or from package root
if [ -f "${SERVER_DIR}/launch.py" ]; then
    PACKAGE_DIR="$SERVER_DIR"
elif [ -f "${SCRIPT_DIR}/../../launch.py" ]; then
    PACKAGE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
else
    echo "Error: Cannot find NormCode server files"
    echo "Run this script from the normcode-server directory"
    exit 1
fi

DEFAULT_INSTALL_DIR="/home/ubuntu/apps/normcode/normcode-server"
DEFAULT_PORT=8080
DEFAULT_USER=$(whoami)
PYTHON_CMD="python3"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ─── Parse Arguments ─────────────────────────────────────────────────────
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
PORT="$DEFAULT_PORT"
SKIP_NGINX=false
SKIP_SYSTEMD=false
UPDATE_ONLY=false
UNINSTALL=false
DOMAIN=""
NONINTERACTIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)    INSTALL_DIR="$2"; shift 2 ;;
        --port)           PORT="$2"; shift 2 ;;
        --domain)         DOMAIN="$2"; shift 2 ;;
        --user)           DEFAULT_USER="$2"; shift 2 ;;
        --skip-nginx)     SKIP_NGINX=true; shift ;;
        --skip-systemd)   SKIP_SYSTEMD=true; shift ;;
        --update)         UPDATE_ONLY=true; shift ;;
        --uninstall)      UNINSTALL=true; shift ;;
        --yes|-y)         NONINTERACTIVE=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install-dir DIR    Installation directory (default: $DEFAULT_INSTALL_DIR)"
            echo "  --port PORT          Server port (default: $DEFAULT_PORT)"
            echo "  --domain DOMAIN      Domain name for Nginx (default: server IP)"
            echo "  --user USER          System user to run as (default: current user)"
            echo "  --skip-nginx         Skip Nginx configuration"
            echo "  --skip-systemd       Skip systemd service setup"
            echo "  --update             Update existing installation only"
            echo "  --uninstall          Remove service and configuration"
            echo "  --yes, -y            Non-interactive mode (accept defaults)"
            echo "  --help, -h           Show this help"
            exit 0
            ;;
        *)  echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Helper Functions ─────────────────────────────────────────────────────
log()     { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[⚠]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }
info()    { echo -e "${CYAN}[→]${NC} $1"; }
header()  { echo -e "\n${BOLD}═══ $1 ═══${NC}\n"; }

confirm() {
    if [ "$NONINTERACTIVE" = true ]; then
        return 0
    fi
    read -p "$(echo -e "${CYAN}$1 [Y/n]: ${NC}")" -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]
}

# ─── Uninstall ────────────────────────────────────────────────────────────
if [ "$UNINSTALL" = true ]; then
    header "Uninstalling NormCode Server"

    if confirm "Stop and disable systemd service?"; then
        sudo systemctl stop normcode 2>/dev/null || true
        sudo systemctl disable normcode 2>/dev/null || true
        sudo rm -f /etc/systemd/system/normcode.service
        sudo systemctl daemon-reload
        log "Systemd service removed"
    fi

    if confirm "Remove Nginx configuration?"; then
        sudo rm -f /etc/nginx/sites-enabled/normcode
        sudo rm -f /etc/nginx/sites-available/normcode
        sudo nginx -t 2>/dev/null && sudo systemctl reload nginx 2>/dev/null || true
        log "Nginx configuration removed"
    fi

    if confirm "Remove logrotate configuration?"; then
        sudo rm -f /etc/logrotate.d/normcode
        log "Logrotate configuration removed"
    fi

    warn "Installation directory NOT removed: ${INSTALL_DIR}"
    warn "Remove manually if desired: rm -rf ${INSTALL_DIR}"
    log "Uninstall complete"
    exit 0
fi

# ─── Banner ───────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║    NormCode Server - Deployment Script       ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${DIM}Package:${NC}   ${PACKAGE_DIR}"
echo -e "  ${DIM}Target:${NC}    ${INSTALL_DIR}"
echo -e "  ${DIM}Port:${NC}      ${PORT}"
echo -e "  ${DIM}User:${NC}      ${DEFAULT_USER}"
echo ""

if ! confirm "Proceed with deployment?"; then
    echo "Deployment cancelled."
    exit 0
fi

# ==========================================================================
# Step 1: System Prerequisites
# ==========================================================================
header "Step 1: Checking System Prerequisites"

# Check Python 3.8+
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 8 ]; then
        log "Python ${PY_VERSION} found"
    else
        error "Python 3.8+ required, found ${PY_VERSION}"
        exit 1
    fi
else
    error "Python 3 not found. Install with: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Check pip
if python3 -m pip --version &>/dev/null; then
    log "pip found"
else
    warn "pip not found, installing..."
    sudo apt-get install -y python3-pip
fi

# Check venv module
if python3 -c "import venv" &>/dev/null; then
    log "venv module found"
else
    warn "venv not found, installing..."
    sudo apt-get install -y python3-venv
fi

# Check nginx (optional)
if [ "$SKIP_NGINX" = false ]; then
    if command -v nginx &>/dev/null; then
        log "Nginx found: $(nginx -v 2>&1 | head -1)"
    else
        if confirm "Nginx not found. Install it?"; then
            sudo apt-get update && sudo apt-get install -y nginx
            log "Nginx installed"
        else
            SKIP_NGINX=true
            warn "Skipping Nginx setup"
        fi
    fi
fi

# ==========================================================================
# Step 2: Installation Directory
# ==========================================================================
header "Step 2: Setting Up Installation Directory"

if [ "$UPDATE_ONLY" = true ] && [ ! -d "$INSTALL_DIR" ]; then
    error "Installation directory not found: $INSTALL_DIR"
    error "Cannot update - run without --update for fresh install"
    exit 1
fi

# Create directory if needed
mkdir -p "$INSTALL_DIR"

# Copy/sync files
if [ "$(realpath "$PACKAGE_DIR")" != "$(realpath "$INSTALL_DIR")" ]; then
    info "Syncing files to ${INSTALL_DIR}..."
    rsync -av --exclude='venv' --exclude='data/plans/*' --exclude='data/runs/*' \
          --exclude='data/config/settings.yaml' --exclude='__pycache__' \
          "${PACKAGE_DIR}/" "${INSTALL_DIR}/"
    log "Files synced"
else
    log "Running from install directory"
fi

# Create data directories
mkdir -p "${INSTALL_DIR}/data/plans"
mkdir -p "${INSTALL_DIR}/data/runs"
mkdir -p "${INSTALL_DIR}/data/config"
log "Data directories ready"

# ==========================================================================
# Step 3: Virtual Environment & Dependencies
# ==========================================================================
header "Step 3: Python Virtual Environment"

VENV_DIR="${INSTALL_DIR}/venv"

if [ -d "$VENV_DIR" ]; then
    if [ "$UPDATE_ONLY" = true ]; then
        log "Using existing virtual environment"
    else
        if confirm "Virtual environment exists. Recreate?"; then
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
            log "Virtual environment recreated"
        else
            log "Using existing virtual environment"
        fi
    fi
else
    python3 -m venv "$VENV_DIR"
    log "Virtual environment created: ${VENV_DIR}"
fi

# Activate and install
info "Installing Python dependencies..."
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet
pip install -r "${INSTALL_DIR}/requirements.txt" --quiet
log "Dependencies installed"

# Verify critical imports
python3 -c "import fastapi; import uvicorn; import yaml; print('All imports OK')" || {
    error "Critical imports failed!"
    exit 1
}
log "Import verification passed"

deactivate

# ==========================================================================
# Step 4: Configuration
# ==========================================================================
header "Step 4: Configuration"

SETTINGS_FILE="${INSTALL_DIR}/data/config/settings.yaml"
SETTINGS_TEMPLATE="${INSTALL_DIR}/data/config/settings.yaml.template"

if [ -f "$SETTINGS_FILE" ]; then
    log "Settings file exists: ${SETTINGS_FILE}"
elif [ -f "$SETTINGS_TEMPLATE" ]; then
    cp "$SETTINGS_TEMPLATE" "$SETTINGS_FILE"
    warn "Created settings from template - edit to add your API keys:"
    warn "  ${SETTINGS_FILE}"
else
    warn "No settings template found. Server will use demo mode only."
fi

# Run validation if available
VALIDATE_SCRIPT="${INSTALL_DIR}/scripts/deploy/validate_config.py"
if [ -f "$VALIDATE_SCRIPT" ]; then
    info "Validating configuration..."
    source "${VENV_DIR}/bin/activate"
    python3 "$VALIDATE_SCRIPT" --install-dir "$INSTALL_DIR" --port "$PORT" || {
        warn "Configuration validation found issues (see above)"
    }
    deactivate
fi

# ==========================================================================
# Step 5: Systemd Service
# ==========================================================================
if [ "$SKIP_SYSTEMD" = false ]; then
    header "Step 5: Systemd Service"

    SERVICE_FILE="/etc/systemd/system/normcode.service"

    # Generate service file with actual paths
    info "Creating systemd service..."
    sudo tee "$SERVICE_FILE" > /dev/null << SYSTEMD_EOF
[Unit]
Description=NormCode Deployment Server
Documentation=https://github.com/your-org/normcode
After=network.target nginx.service
Wants=network-online.target

[Service]
Type=simple
User=${DEFAULT_USER}
Group=${DEFAULT_USER}

WorkingDirectory=${INSTALL_DIR}

Environment="NORMCODE_HOST=0.0.0.0"
Environment="NORMCODE_PORT=${PORT}"
Environment="NORMCODE_PLANS_DIR=${INSTALL_DIR}/data/plans"
Environment="NORMCODE_RUNS_DIR=${INSTALL_DIR}/data/runs"
Environment="NORMCODE_LOG_LEVEL=INFO"

ExecStart=${VENV_DIR}/bin/python3 launch.py --quick --host 0.0.0.0 --port ${PORT}

Restart=always
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=5

TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGINT

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=${INSTALL_DIR}/data

StandardOutput=journal
StandardError=journal
SyslogIdentifier=normcode

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

    sudo systemctl daemon-reload
    sudo systemctl enable normcode
    log "Systemd service created and enabled"

    # Start or restart
    if systemctl is-active --quiet normcode 2>/dev/null; then
        info "Restarting NormCode service..."
        sudo systemctl restart normcode
    else
        info "Starting NormCode service..."
        sudo systemctl start normcode
    fi

    # Wait and check
    sleep 3
    if systemctl is-active --quiet normcode; then
        log "NormCode service is running"
    else
        error "Service failed to start! Check logs:"
        error "  sudo journalctl -u normcode -n 50 --no-pager"
        sudo journalctl -u normcode -n 20 --no-pager
    fi
else
    header "Step 5: Systemd Service (SKIPPED)"
    warn "Skipping systemd setup. Start manually:"
    warn "  cd ${INSTALL_DIR} && source venv/bin/activate && python3 launch.py --quick"
fi

# ==========================================================================
# Step 6: Nginx Configuration
# ==========================================================================
if [ "$SKIP_NGINX" = false ]; then
    header "Step 6: Nginx Reverse Proxy"

    # Determine server name
    if [ -z "$DOMAIN" ]; then
        SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        DOMAIN="$SERVER_IP"
        info "No domain specified, using IP: ${DOMAIN}"
    fi

    NGINX_CONF="/etc/nginx/sites-available/normcode"

    info "Creating Nginx configuration..."
    sudo tee "$NGINX_CONF" > /dev/null << NGINX_EOF
# NormCode Server - Generated by deploy.sh on $(date)
limit_req_zone \$binary_remote_addr zone=normcode_api:10m rate=30r/s;
limit_req_zone \$binary_remote_addr zone=normcode_upload:10m rate=5r/m;

upstream normcode_backend {
    server 127.0.0.1:${PORT};
    keepalive 32;
}

server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 200M;

    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header Connection "";

    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # SSE endpoints - disable buffering
    location ~ ^/api/(monitor/stream|runs/.*/stream|userbenches/.*/events/stream|inputs/stream) {
        proxy_pass http://normcode_backend;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # WebSocket endpoints
    location ~ ^/ws/ {
        proxy_pass http://normcode_backend;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }

    # File upload endpoint
    location = /api/plans/deploy-file {
        proxy_pass http://normcode_backend;
        client_max_body_size 200M;
        proxy_request_buffering off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        limit_req zone=normcode_upload burst=3 nodelay;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://normcode_backend;
        limit_req zone=normcode_api burst=50 nodelay;
    }

    # All other routes
    location / {
        proxy_pass http://normcode_backend;
        limit_req zone=normcode_api burst=50 nodelay;
    }

    # Return JSON error when backend is down
    error_page 502 503 504 @backend_down;
    location @backend_down {
        default_type application/json;
        return 502 '{"error": "NormCode server is not running", "detail": "Backend service unavailable. Run: sudo systemctl status normcode"}';
    }

    access_log /var/log/nginx/normcode_access.log;
    error_log /var/log/nginx/normcode_error.log;
}
NGINX_EOF

    # Enable site
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/normcode

    # Remove default site if it conflicts
    if [ -f /etc/nginx/sites-enabled/default ]; then
        if confirm "Remove default Nginx site? (may conflict on port 80)"; then
            sudo rm -f /etc/nginx/sites-enabled/default
            log "Default Nginx site removed"
        fi
    fi

    # Test and reload
    if sudo nginx -t 2>&1; then
        sudo systemctl reload nginx
        log "Nginx configured and reloaded"
    else
        error "Nginx configuration test failed!"
        error "Fix manually: sudo nano ${NGINX_CONF}"
    fi
else
    header "Step 6: Nginx (SKIPPED)"
fi

# ==========================================================================
# Step 7: Log Rotation
# ==========================================================================
header "Step 7: Log Rotation"

sudo tee /etc/logrotate.d/normcode > /dev/null << LOGROTATE_EOF
${INSTALL_DIR}/data/runs/*/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 ${DEFAULT_USER} ${DEFAULT_USER}
    maxsize 50M
}
LOGROTATE_EOF

log "Log rotation configured"

# ==========================================================================
# Step 8: Health Check & Summary
# ==========================================================================
header "Step 8: Final Health Check"

sleep 2

# Direct backend check
BACKEND_OK=false
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --connect-timeout 10 \
    "http://127.0.0.1:${PORT}/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    log "Backend health check: OK (HTTP 200)"
    BACKEND_OK=true
else
    warn "Backend health check: HTTP ${HTTP_CODE}"
fi

# Nginx check (if configured)
if [ "$SKIP_NGINX" = false ]; then
    NGINX_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 10 \
        "http://${DOMAIN}/health" 2>/dev/null || echo "000")

    if [ "$NGINX_CODE" = "200" ]; then
        log "Nginx proxy check: OK (HTTP 200)"
    else
        warn "Nginx proxy check: HTTP ${NGINX_CODE}"
    fi
fi

# API check
if [ "$BACKEND_OK" = true ]; then
    PLANS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 10 \
        "http://127.0.0.1:${PORT}/api/plans" 2>/dev/null || echo "000")

    if [ "$PLANS_CODE" = "200" ]; then
        log "API check (/api/plans): OK"
    else
        warn "API check: HTTP ${PLANS_CODE}"
    fi
fi

# ==========================================================================
# Summary
# ==========================================================================
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║       Deployment Complete!                    ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Installation:${NC}  ${INSTALL_DIR}"
echo -e "  ${BOLD}Port:${NC}          ${PORT}"
echo -e "  ${BOLD}User:${NC}          ${DEFAULT_USER}"
echo -e "  ${BOLD}Venv:${NC}          ${VENV_DIR}"
echo ""
echo -e "  ${BOLD}Useful Commands:${NC}"
echo -e "    ${CYAN}sudo systemctl status normcode${NC}     # Check service status"
echo -e "    ${CYAN}sudo systemctl restart normcode${NC}    # Restart server"
echo -e "    ${CYAN}sudo journalctl -u normcode -f${NC}     # Follow logs"
echo -e "    ${CYAN}sudo nginx -t && sudo systemctl reload nginx${NC}  # Reload Nginx"
echo ""
echo -e "  ${BOLD}Access:${NC}"
echo -e "    Dashboard:  ${GREEN}http://${DOMAIN}/dashboard${NC}"
echo -e "    API Docs:   ${GREEN}http://${DOMAIN}/docs${NC}"
echo -e "    Direct API: ${GREEN}http://${DOMAIN}:${PORT}/health${NC}"
echo ""
echo -e "  ${BOLD}Settings:${NC}"
echo -e "    Edit LLM API keys: ${DIM}${SETTINGS_FILE}${NC}"
echo ""


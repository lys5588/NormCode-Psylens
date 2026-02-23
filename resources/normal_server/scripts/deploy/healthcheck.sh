#!/bin/bash
# =============================================================================
# NormCode Server Health Check Script
# =============================================================================
#
# Usage:
#   ./healthcheck.sh                     # Check default (localhost:8080)
#   ./healthcheck.sh --host 10.0.0.5     # Check specific host
#   ./healthcheck.sh --port 9000         # Check specific port
#   ./healthcheck.sh --alert             # Send alert on failure (needs config)
#   ./healthcheck.sh --verbose           # Detailed output
#
# Cron example (check every 5 minutes):
#   */5 * * * * /home/ubuntu/apps/normcode/normcode-server/scripts/deploy/healthcheck.sh --alert >> /var/log/normcode-health.log 2>&1
#
# =============================================================================

set -euo pipefail

# Defaults
HOST="127.0.0.1"
PORT="8080"
ALERT=false
VERBOSE=false
TIMEOUT=10
RESTART_ON_FAIL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)     HOST="$2"; shift 2 ;;
        --port)     PORT="$2"; shift 2 ;;
        --alert)    ALERT=true; shift ;;
        --verbose)  VERBOSE=true; shift ;;
        --restart)  RESTART_ON_FAIL=true; shift ;;
        --timeout)  TIMEOUT="$2"; shift 2 ;;
        *)          echo "Unknown option: $1"; exit 1 ;;
    esac
done

BASE_URL="http://${HOST}:${PORT}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HEALTH_OK=true
ISSUES=()

log() {
    echo "[${TIMESTAMP}] $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo "  $1"
    fi
}

# ─── Check 1: Service status (systemd) ───────────────────────────────────
check_service() {
    if systemctl is-active --quiet normcode 2>/dev/null; then
        log_verbose "✓ systemd service: active"
    else
        HEALTH_OK=false
        ISSUES+=("systemd service is not active")
        log_verbose "✗ systemd service: inactive"
    fi
}

# ─── Check 2: HTTP health endpoint ───────────────────────────────────────
check_health_endpoint() {
    local response
    local http_code

    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout "$TIMEOUT" \
        "${BASE_URL}/health" 2>/dev/null || echo "000")

    if [ "$http_code" = "200" ]; then
        log_verbose "✓ /health endpoint: HTTP 200"

        # Parse response for details
        if [ "$VERBOSE" = true ]; then
            response=$(curl -s --connect-timeout "$TIMEOUT" "${BASE_URL}/health" 2>/dev/null)
            log_verbose "  Response: $response"
        fi
    else
        HEALTH_OK=false
        ISSUES+=("/health returned HTTP ${http_code}")
        log_verbose "✗ /health endpoint: HTTP ${http_code}"
    fi
}

# ─── Check 3: API responsiveness ─────────────────────────────────────────
check_api() {
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout "$TIMEOUT" \
        "${BASE_URL}/api/plans" 2>/dev/null || echo "000")

    if [ "$http_code" = "200" ]; then
        log_verbose "✓ /api/plans endpoint: HTTP 200"
    else
        HEALTH_OK=false
        ISSUES+=("/api/plans returned HTTP ${http_code}")
        log_verbose "✗ /api/plans endpoint: HTTP ${http_code}"
    fi
}

# ─── Check 4: Port is listening ──────────────────────────────────────────
check_port() {
    if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        log_verbose "✓ Port ${PORT}: listening"
    elif netstat -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        log_verbose "✓ Port ${PORT}: listening"
    else
        HEALTH_OK=false
        ISSUES+=("Port ${PORT} is not listening")
        log_verbose "✗ Port ${PORT}: not listening"
    fi
}

# ─── Check 5: Disk space ─────────────────────────────────────────────────
check_disk() {
    local usage
    usage=$(df --output=pcent / 2>/dev/null | tail -1 | tr -d ' %')

    if [ -n "$usage" ] && [ "$usage" -lt 90 ]; then
        log_verbose "✓ Disk usage: ${usage}%"
    elif [ -n "$usage" ]; then
        HEALTH_OK=false
        ISSUES+=("Disk usage is ${usage}% (>90%)")
        log_verbose "✗ Disk usage: ${usage}% (critical!)"
    fi
}

# ─── Check 6: Memory usage ───────────────────────────────────────────────
check_memory() {
    local mem_available
    mem_available=$(free -m 2>/dev/null | awk '/^Mem:/ {print $7}')

    if [ -n "$mem_available" ] && [ "$mem_available" -gt 256 ]; then
        log_verbose "✓ Available memory: ${mem_available}MB"
    elif [ -n "$mem_available" ]; then
        ISSUES+=("Low memory: ${mem_available}MB available")
        log_verbose "⚠ Available memory: ${mem_available}MB (low)"
    fi
}

# ─── Check 7: Nginx status ───────────────────────────────────────────────
check_nginx() {
    if systemctl is-active --quiet nginx 2>/dev/null; then
        log_verbose "✓ Nginx: active"
    elif command -v nginx &>/dev/null; then
        ISSUES+=("Nginx is installed but not running")
        log_verbose "⚠ Nginx: installed but not active"
    else
        log_verbose "○ Nginx: not installed (direct access mode)"
    fi
}

# ─── Run all checks ──────────────────────────────────────────────────────
log "Starting health check for ${BASE_URL}"

check_service
check_port
check_health_endpoint
check_api
check_disk
check_memory
check_nginx

# ─── Report results ──────────────────────────────────────────────────────
if [ "$HEALTH_OK" = true ]; then
    log "HEALTHY ✓ - All checks passed"
    exit 0
else
    log "UNHEALTHY ✗ - Issues found:"
    for issue in "${ISSUES[@]}"; do
        log "  • $issue"
    done

    # Auto-restart if enabled
    if [ "$RESTART_ON_FAIL" = true ]; then
        log "Attempting auto-restart..."
        if sudo systemctl restart normcode 2>/dev/null; then
            sleep 5
            # Re-check after restart
            http_code=$(curl -s -o /dev/null -w "%{http_code}" \
                --connect-timeout "$TIMEOUT" \
                "${BASE_URL}/health" 2>/dev/null || echo "000")
            if [ "$http_code" = "200" ]; then
                log "Auto-restart SUCCEEDED ✓"
            else
                log "Auto-restart FAILED ✗ - manual intervention needed"
            fi
        else
            log "Auto-restart FAILED ✗ - insufficient permissions"
        fi
    fi

    # Alert (placeholder - customize for your alerting system)
    if [ "$ALERT" = true ]; then
        # Uncomment and configure one of these:

        # --- Slack webhook ---
        # SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        # curl -s -X POST "$SLACK_WEBHOOK" \
        #     -H 'Content-type: application/json' \
        #     -d "{\"text\":\"🚨 NormCode Server UNHEALTHY on $(hostname): ${ISSUES[*]}\"}"

        # --- Email via mailutils ---
        # echo "NormCode Server Issues: ${ISSUES[*]}" | mail -s "🚨 NormCode Health Alert" admin@example.com

        # --- Write to alert file ---
        echo "[${TIMESTAMP}] ALERT: ${ISSUES[*]}" >> /tmp/normcode-alerts.log

        log "Alert dispatched"
    fi

    exit 1
fi


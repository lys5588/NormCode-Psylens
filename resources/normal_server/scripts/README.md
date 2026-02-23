# NormCode Server Scripts

Utility scripts and standalone tools for the NormCode Deployment Server.

## Core Scripts

### `runner.py`
Standalone CLI runner for executing NormCode plans without the Canvas App.

**Usage:**
```bash
python scripts/runner.py ./path/to/project.normcode-canvas.json
python scripts/runner.py ./path/to/project.normcode-canvas.json --resume
python scripts/runner.py ./path/to/project.normcode-canvas.json --llm gpt-4o
```

**Features:**
- Execute plans from `.normcode-canvas.json` or `manifest.json`
- Resume from checkpoints
- Override LLM models and max cycles
- Use deployment-local tools
- Export results to JSON

### `start_server.py`
Simple server starter script (alternative to `launch.py`).

**Usage:**
```bash
python scripts/start_server.py
python scripts/start_server.py --port 9000
python scripts/start_server.py --host 127.0.0.1
```

**Note:** For more features (dependency checking, configuration, dashboard), use `launch.py` in the parent directory instead.

## UI Window Scripts

These scripts launch dedicated windows for the server UI using `pywebview`.

### `server_window.py`
Opens the main server dashboard in a dedicated window.

**Usage:**
```bash
python scripts/server_window.py
python scripts/server_window.py --port 8080 --host localhost
```

**Requires:** `pip install pywebview`

### `monitor_window.py`
Opens the legacy monitor UI in a dedicated window (replaced by unified server dashboard).

**Usage:**
```bash
python scripts/monitor_window.py
python scripts/monitor_window.py --port 8080
```

**Requires:** `pip install pywebview`

## Monitoring Tools

### `monitor.py`
Terminal-based (TUI) monitor for real-time server activity.

**Usage:**
```bash
python scripts/monitor.py
python scripts/monitor.py --server http://localhost:8080
python scripts/monitor.py --compact  # For smaller terminals
```

**Features:**
- Real-time event streaming
- Active runs tracking
- LLM call statistics
- Statistics dashboard
- Runs with or without Rich TUI library

**Requires:** `pip install rich requests` (optional: falls back to simple mode)

## Packaging Tools

### `pack.py`
Package NormCode projects into deployment-ready zip files.

**Usage:**
```bash
python scripts/pack.py ./path/to/project.normcode-canvas.json
python scripts/pack.py ./path/to/project.normcode-canvas.json --output my-plan.zip
```

**Features:**
- Creates self-contained plan packages
- Includes all necessary files (repos, provisions, manifests)
- Ready for deployment via HTTP upload or directory copy

## Directory Structure

After organizing:

```
normal_server/
├── server.py              # Main FastAPI server
├── launch.py              # Full-featured launcher with menu
├── scripts/               # ← All utility scripts here
│   ├── runner.py          # Standalone plan runner
│   ├── start_server.py    # Simple server starter
│   ├── server_window.py   # Dashboard window launcher
│   ├── monitor_window.py  # Monitor window launcher
│   ├── monitor.py         # TUI monitor
│   ├── pack.py            # Plan packager
│   └── README.md          # This file
├── routes/                # API endpoints
├── service/               # Business logic
├── static/                # Web UI assets
├── tools/                 # Deployment tools
├── mock_users/            # Test clients
└── data/                  # Runtime data
    ├── plans/             # Deployed plans
    ├── runs/              # Execution data
    └── config/            # Settings
```

## Quick Start

1. **Start the server (recommended):**
   ```bash
   python launch.py --quick
   ```

2. **Or use the simple starter:**
   ```bash
   python scripts/start_server.py
   ```

3. **Run a plan standalone:**
   ```bash
   python scripts/runner.py path/to/plan.normcode-canvas.json
   ```

4. **Monitor a running server:**
   ```bash
   python scripts/monitor.py --server http://localhost:8080
   ```

## See Also

- Main server documentation: `../README.md`
- API documentation: http://localhost:8080/docs
- Server dashboard: http://localhost:8080/server/ui

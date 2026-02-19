# NormCode Tools

**User-facing tools and interfaces for working with NormCode plans.**

---

## Overview

This section documents the tools that enable users to create, execute, debug, and audit NormCode plans. The primary tool is the **Graph Canvas App**—a unified visual interface that brings together all aspects of working with NormCode.

---

## The Graph Canvas App

The Graph Canvas App is a standalone React/FastAPI application designed around a core principle: **the inference graph IS the interface**.

### Current Status: ✅ Production Ready (v0.8.0)

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1**: Foundation | ✅ Complete | Graph display, node visualization |
| **Phase 2**: Execution | ✅ Complete | Real-time execution, WebSocket events |
| **Phase 3**: Debugging | ✅ Complete | Breakpoints, stepping, tensor inspection |
| **Phase 4**: Modification | ✅ Complete | Value override, function modification, selective re-run |
| **Phase 5**: Polish | 🔄 In Progress | Keyboard shortcuts, search, export |

### Key Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| **Visualize** | ✅ | See the full inference graph with function and value nodes |
| **Execute** | ✅ | Run plans with live progress on the graph |
| **Debug** | ✅ | Set breakpoints, step through, inspect state |
| **Inspect** | ✅ | View tensors, logs, and execution context at any node |
| **Project Management** | ✅ | IDE-like project system with persistence |
| **Multi-Agent** | ✅ | Configure multiple agents with different LLMs |
| **Editor** | ✅ | Integrated NormCode file editor |
| **Modify** | ✅ | Override values, change paradigms, selective re-run |
| **Checkpoint/Resume** | ✅ | Resume or fork from saved checkpoints |

---

## Documentation

### User Documentation

| Document | Description |
|----------|-------------|
| **[Canvas App Overview](canvas_app_overview.md)** | Architecture, concepts, and system design |
| **[Canvas App User Guide](canvas_app_user_guide.md)** | Complete usage guide with screenshots |
| **[Canvas App API Reference](canvas_app_api_reference.md)** | REST API, WebSocket events, and stores |

### Planning & Development

| Document | Description |
|----------|-------------|
| **[Implementation Plan](implementation_plan.md)** | Remaining work and roadmap |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### LLM Configuration (settings.yaml)

Create `settings.yaml` in the project root to configure LLM API keys:

```yaml
qwen-plus:
    DASHSCOPE_API_KEY: sk-your-api-key-here

gpt-4o:
    OPENAI_API_KEY: sk-your-openai-key-here

claude-3-sonnet:
    ANTHROPIC_API_KEY: sk-your-anthropic-key-here
```

**Note**: The `demo` mode is always available without an API key for testing.

### Running the App

```powershell
# From project root
cd canvas_app
python launch.py
```

The launcher automatically checks and installs dependencies on first run.

**Launcher Options:**
```powershell
python launch.py              # Start in dev mode (default)
python launch.py --prod       # Production mode (no auto-reload)
python launch.py --install    # Force reinstall all dependencies
python launch.py --skip-deps  # Skip dependency checks (faster startup)
python launch.py --backend-only   # Only start backend
python launch.py --frontend-only  # Only start frontend
python launch.py --kill       # Kill existing servers before starting
```

**Access Points:**
- **App**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/events

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CANVAS APP                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript + Vite)                                    │
│  ├── Graph Canvas (React Flow)                                          │
│  ├── Control Panel (execution controls)                                 │
│  ├── Detail Panel (node inspection, tensor viewer)                      │
│  ├── Agent Panel (multi-agent configuration)                            │
│  ├── Editor Panel (NormCode file editing)                               │
│  ├── Log Panel (real-time execution logs)                               │
│  └── Project Panel (project management)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python)                                              │
│  ├── Execution Service (Orchestrator wrapper)                           │
│  ├── Graph Service (graph building & layout)                            │
│  ├── Agent Service (multi-agent registry)                               │
│  ├── Project Service (project management)                               │
│  └── WebSocket Events (real-time updates)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  NormCode Infrastructure (infra/)                                        │
│  ├── Orchestrator (execution engine)                                    │
│  ├── ConceptRepo / InferenceRepo                                        │
│  └── Agent Body & Tools                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Two Node Types

The graph displays two fundamentally different kinds of nodes:

### Value Nodes (Data)
- Contain **References** (multi-dimensional tensors)
- Show **axes**, **shape**, and **data preview**
- Represent the data flowing through the plan
- Expandable to show full tensor contents via TensorInspector

### Function Nodes (Operations)
- Contain **sequences** (imperative, grouping, looping, etc.)
- Show **paradigm** and **working interpretation**
- Represent the operations transforming data
- Expandable to show execution pipeline status

---

## Execution Control

### Control Actions

| Control | Description |
|---------|-------------|
| **▶ Run** | Execute all ready inferences |
| **⏸ Pause** | Stop after current inference |
| **⏭ Step** | Execute exactly one inference |
| **🎯 Run to** | Execute until selected node |
| **🔄 Reset** | Reset execution and start fresh |

### Breakpoints

| Type | Behavior |
|------|----------|
| **Unconditional** | Always pause at this node |
| **Per-node toggle** | Click BP button in detail panel |

---

## Project Management

The canvas app operates like an IDE with project-based workflow:

- **Project Config**: `{name}.normcode-canvas.json` in project directory
- **Project Registry**: `~/.normcode-canvas/project-registry.json`
- **Multiple Projects**: Same directory can have multiple project configs
- **Persistence**: Breakpoints, settings, and state saved per project

---

## Relationship to Other Sections

| Section | Relationship |
|---------|--------------|
| **[2. Grammar](../2_grammar/README.md)** | Tools work with `.ncd` format (via compilation) |
| **[3. Execution](../3_execution/README.md)** | Tools integrate with Orchestrator |
| **[4. Compilation](../4_compilation/README.md)** | Tools load compiled repositories |

---

## Legacy Tools

While the Graph Canvas App is the primary tool, legacy tools include:

| Tool | Location | Description |
|------|----------|-------------|
| **CLI Orchestrator** | `cli_orchestrator.py` | Command-line execution |
| **Streamlit App** | `streamlit_app/` | Web UI for execution (legacy) |
| **Editor App** | `editor_app/` | React/FastAPI editor (legacy) |

---

## Next Steps

See the [Implementation Plan](implementation_plan.md) for remaining work and roadmap.

---

**Version**: 0.8.0  
**Last Updated**: January 2026

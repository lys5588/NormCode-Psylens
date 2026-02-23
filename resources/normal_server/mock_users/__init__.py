"""
Mock Users Package

Test clients and scenarios for the NormCode Deployment Server.

Available modules:
- client.py: CLI client for basic server interaction
- client_gui.py: Tkinter GUI client (basic)
- client_ui.py: Modern web-based client (pywebview/browser)
- watch_client.py: Rich TUI for watching run execution
- scenarios.py: Automated test scenarios

Usage:
    python -m mock_users.client plans              # List plans (CLI)
    python -m mock_users.client_ui                 # Open client UI (pywebview)
    python -m mock_users.watch_client <run_id>     # Watch a run (TUI)
    python -m mock_users.scenarios run all         # Run all tests

Web UIs available when server is running:
    http://localhost:8080/client/ui     # Client UI
    http://localhost:8080/monitor/ui    # Monitor UI

For dedicated plan clients, see the mock_clients package at project root.
"""

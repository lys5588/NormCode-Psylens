"""
API Routes Package

Modular route definitions for the NormCode server.
"""


def include_all_routes(app):
    """Include all route modules in the app."""
    # Import here to avoid circular imports and support both package and direct run
    from routes.health import router as health_router
    from routes.plans import router as plans_router
    from routes.runs import router as runs_router
    from routes.db_inspector import router as db_inspector_router
    from routes.streaming import router as streaming_router
    from routes.monitor import router as monitor_router
    from routes.server_ui import router as server_ui_router
    from routes.files import router as files_router
    from routes.user_input import router as user_input_router
    # Legacy UI routes (kept for backwards compatibility)
    from routes.monitor_ui import router as monitor_ui_router
    from routes.client_ui import router as client_ui_router
    # PPT client UI
    from routes.ppt_client import router as ppt_client_router
    # Tools API
    from routes.tools import router as tools_router
    
    app.include_router(health_router)
    app.include_router(plans_router, prefix="/api/plans", tags=["plans"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    app.include_router(db_inspector_router, tags=["db-inspector"])
    app.include_router(streaming_router, tags=["streaming"])
    app.include_router(monitor_router, prefix="/api/monitor", tags=["monitor"])
    # Files API for client workspace access
    app.include_router(files_router, prefix="/api", tags=["files"])
    # User Input API for human-in-the-loop
    app.include_router(user_input_router, prefix="/api", tags=["user-input"])
    # Main unified dashboard
    app.include_router(server_ui_router, tags=["server-ui"])
    # Legacy routes (redirect or keep for compatibility)
    app.include_router(monitor_ui_router, prefix="/monitor", tags=["monitor-ui"])
    app.include_router(client_ui_router, prefix="/client", tags=["client-ui"])
    # PPT client for presentation generation
    app.include_router(ppt_client_router, prefix="/ppt", tags=["ppt-client"])
    # Tools inspection and testing
    app.include_router(tools_router, prefix="/api/tools", tags=["tools"])


"""Main CLI entrypoint to run the FastAPI application."""

import sys
import uvicorn
from experiment_manager.api import app


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the Uvicorn ASGI server."""
    print(f"Starting Scientific Experiments REST API on http://{host}:{port}")
    print(f"Interactive Swagger documentation: http://{host}:{port}/docs")
    print(f"ReDoc documentation: http://{host}:{port}/redoc")
    uvicorn.run("experiment_manager.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    host_arg = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    run_server(host=host_arg, port=port_arg)

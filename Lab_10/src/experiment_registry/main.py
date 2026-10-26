"""CLI entry point and production server launcher."""

from __future__ import annotations

import argparse

import uvicorn

from . import __version__
from .config import get_settings


def parse_args(args=None):
    """Parse command line arguments."""
    settings = get_settings()
    parser = argparse.ArgumentParser(
        prog="experiment-registry",
        description="Production REST API service for scientific experiments registry",
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help=f"Host interface to bind (default: {settings.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port number to bind (default: {settings.port})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.is_development,
        help="Enable auto-reload for local development",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(args)


def main():
    """Main CLI execution handler."""
    args = parse_args()
    settings = get_settings()

    print("============================================================")
    print(f"  {settings.app_name} v{__version__}")
    print(f"  Environment : {settings.environment}")
    print(f"  Server URL  : http://{args.host}:{args.port}")
    print(f"  Swagger UI  : http://{args.host}:{args.port}/docs")
    print(f"  Health Check: http://{args.host}:{args.port}/health")
    print("============================================================")

    uvicorn.run(
        "experiment_registry.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

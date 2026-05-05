from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PROXY_ENV_NAMES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def clear_proxy_env() -> None:
    for name in PROXY_ENV_NAMES:
        os.environ.pop(name, None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the AgentFlow Lite backend MVP.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8010, help="Port to bind. Defaults to 8010.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload for development.")
    parser.add_argument(
        "--keep-proxy",
        action="store_true",
        help="Keep current HTTP/HTTPS proxy environment variables.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    if not args.keep_proxy:
        clear_proxy_env()

    import uvicorn

    print("Starting AgentFlow Lite backend MVP")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Workbench: http://{args.host}:{args.port}/")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"Health:   http://{args.host}:{args.port}/api/health")

    uvicorn.run(
        "backend.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(PROJECT_ROOT),
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env sh
set -eu

python - <<'PY'
import os
import socket
import sys
import time

host = os.getenv("DB_HOST", "mysql")
port = int(os.getenv("DB_PORT", "3306"))
deadline = time.time() + int(os.getenv("DB_WAIT_TIMEOUT", "90"))

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"Database is reachable at {host}:{port}")
            break
    except OSError as exc:
        if time.time() >= deadline:
            print(f"Timed out waiting for database at {host}:{port}: {exc}", file=sys.stderr)
            raise
        print(f"Waiting for database at {host}:{port}...")
        time.sleep(2)
PY

if [ "${1:-}" = "python" ] && [ "${2:-}" = "manage.py" ] && [ "${3:-}" = "runserver" ]; then
    python manage.py migrate --noinput
fi

exec "$@"

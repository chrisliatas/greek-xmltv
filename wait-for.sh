#!/bin/sh
set -eu

TIMEOUT="${TIMEOUT:-15}"

usage() {
  echo "Usage: $0 host:port [-- command args]" >&2
  exit 1
}

if [ "$#" -lt 1 ]; then
  usage
fi

case "$1" in
  *:*)
    HOST="${1%:*}"
    PORT="${1#*:}"
    shift
    ;;
  *)
    usage
    ;;
esac

if [ "${1:-}" = "--" ]; then
  shift
fi

i=0
while [ "$i" -lt "$TIMEOUT" ]; do
  if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
    if [ "$#" -gt 0 ]; then
      exec "$@"
    fi
    exit 0
  fi
  i=$((i + 1))
  sleep 1
done

echo "Timed out waiting for ${HOST}:${PORT} after ${TIMEOUT}s." >&2
exit 1

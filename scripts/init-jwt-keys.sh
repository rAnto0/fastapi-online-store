#!/usr/bin/env bash
set -euo pipefail

bits=2048
force=0
regenerated=0

usage() {
  cat <<'USAGE'
Usage: scripts/init-jwt-keys.sh [--force] [--bits N]

Generates RSA key pair for app.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      shift
      ;;
    --bits)
      bits="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown аргумент: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL не найден. Установи openssl и повтори."
  exit 1
fi

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

app_dir="$root_dir/app/certs"

private_key="$app_dir/jwt-private.pem"
public_key="$app_dir/jwt-public.pem"

mkdir -p "$app_dir"

if [[ -f "$private_key" || -f "$public_key" ]]; then
  if [[ "$force" -ne 1 ]]; then
    echo "Ключи уже существуют: $private_key или $public_key"
    echo "Ничего не делаю. Запусти с --force для пересоздания."
  else
    rm -f "$private_key" "$public_key"
    regenerated=1
  fi
fi

if [[ ! -f "$private_key" || ! -f "$public_key" ]]; then
  echo "Генерирую RSA ключи ($bits бит)..."
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:"$bits" -out "$private_key"
  openssl rsa -in "$private_key" -pubout -out "$public_key"
  chmod 600 "$private_key"
  chmod 644 "$public_key"
  regenerated=1
fi

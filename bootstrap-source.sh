#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .source-v2/part00 ]]; then
  echo "Application source is already expanded."
  exit 0
fi

archive="$(mktemp --suffix=.tar.gz)"
trap 'rm -f "$archive"' EXIT

cat .source-v2/part* | base64 --decode > "$archive"
echo "ace02085a8ca02a0dd39b3ffc2bcb7db58e7229017b19b51e3e9f58ec0c7b859  $archive" | sha256sum -c -
tar -tzf "$archive" >/dev/null
tar -xzf "$archive" -C .

echo "Application source expanded successfully."
echo "Run: docker compose up -d --build"

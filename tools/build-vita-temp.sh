#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
output="${1:-$root/artifacts/Touhou123Vita.vpk}"
: "${VITASDK:?Set VITASDK}"
work="$(mktemp -d /tmp/t123-vita-build.XXXXXX)"
trap 'rm -rf "$work"' EXIT

# VitaSDK's VPK packager mishandles Windows mount paths containing spaces.
cp -a "$root/CMakeLists.txt" "$root/src" "$root/include" "$root/assets" "$work/"
export PATH="$VITASDK/bin:$PATH"
cmake -S "$work" -B "$work/build" -DT123_VITA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build "$work/build" -j2
mkdir -p "$(dirname "$output")"
cp "$work/build/Touhou123Vita.vpk" "$output"
sha256sum "$output"

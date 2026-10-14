#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build-host -DCMAKE_BUILD_TYPE=Debug
cmake --build build-host -j2
ctest --test-dir build-host --output-on-failure
: "${VITASDK:?Set VITASDK}"
export PATH="$VITASDK/bin:$PATH"
cmake -S . -B build-vita -DT123_VITA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-vita -j2
mkdir -p artifacts
cp build-vita/Touhou123Vita.vpk artifacts/Touhou123Vita.vpk

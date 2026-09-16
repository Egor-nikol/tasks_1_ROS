#!/usr/bin/env bash
# Instructor-only local rehearsal, not student preparation.
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -t sda-ros2-l01:2026.1-l01-rc2 .
echo 'Local rehearsal image built. Not yet published or frozen for students.'

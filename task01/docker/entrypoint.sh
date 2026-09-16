#!/usr/bin/env bash
set -e
source /opt/ros/jazzy/setup.bash
source /opt/course_ws/install/setup.bash
mkdir -p "$HOME" "$HOME/.ros"
exec "$@"

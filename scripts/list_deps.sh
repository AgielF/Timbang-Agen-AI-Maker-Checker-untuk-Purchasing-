#!/bin/sh
# POSIX — list Python interpreter info + installed pip packages.
set -eu

echo "== Python =="
python3 --version
command -v python3

echo
echo "== Pip packages (freeze) =="
python3 -m pip freeze

echo
echo "== Optional: dependency tree =="
if python3 -c "import pipdeptree" 2>/dev/null; then
    python3 -m pipdeptree
else
    echo "pipdeptree not installed (pip install pipdeptree)"
fi

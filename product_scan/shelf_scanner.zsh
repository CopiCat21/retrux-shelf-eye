#!/usr/bin/env zsh

# pindah ke folder product_scan relatif dari posisi script
cd "$(dirname "$0")"

# jalankan shelf_scan.py yang ada di folder ini
python shelf_scan.py "$@"

#!/usr/bin/env bash
# Рендер страницы PDF в картинку: tools/page.sh N [dpi]  → печатает путь к jpg
set -e
N=$1; R=${2:-110}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${TMPDIR:-/tmp}/zazulya_page
mkdir -p "$OUT"
pdftoppm -r "$R" -jpeg -f "$N" -l "$N" -singlefile "$ROOT"/01_Лекции/*.pdf "$OUT/стр$(printf %03d "$N")"
echo "$OUT/стр$(printf %03d "$N").jpg"

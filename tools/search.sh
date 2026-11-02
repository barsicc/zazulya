#!/usr/bin/env bash
# Поиск по курсу: tools/search.sh "фраза"   (регистр не важен; фраза ищется и через переносы строк)
# Вывод: выжимки (ШПАРГАЛКА/ВОПРОСЫ/ФОРМУЛЫ/КАРТА/шапки) + страницы полного текста с фрагментом вокруг совпадения.
Q=$1; W=${2:-160}
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
echo "=== Выжимки ==="
grep -n -i -- "$Q" ШПАРГАЛКА.md ВОПРОСЫ.md ФОРМУЛЫ.md КАРТА.md конспекты/_шапки/*.md | cut -c1-260
echo "=== Полный текст: раздел | стр. PDF | фрагмент ==="
python3 - "$Q" "$W" <<'PY'
import sys,re
q=sys.argv[1].lower(); w=int(sys.argv[2])
for line in open("конспекты/_поиск_постранично.txt",encoding="utf-8"):
    code,page,text=line.split(" | ",2)
    low=text.lower(); i=low.find(q)
    while i!=-1:
        print(f"{code} {page}: …{text[max(0,i-w):i+len(q)+w].strip()}…")
        i=low.find(q,i+len(q))
PY

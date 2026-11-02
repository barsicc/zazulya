#!/usr/bin/env python3
"""Извлекает и чистит текстовый слой PDF конспекта (постранично).

Артефакт исходного PDF: символ «D» стоит вместо мягкого переноса, дефиса и минуса
(«обесD\nпечивать», «изDза», «10D6», «СО32D», «ТУ 39D0147»). Скрипт это исправляет.
Выход: build/pages/стрNNN.txt (NNN = номер страницы PDF).

Запуск: python3 tools/extract_text.py
"""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = next((ROOT / "01_Лекции").glob("*.pdf"))
OUT = ROOT / "build" / "pages"
CYR = "А-Яа-яЁё"

def clean(t: str) -> str:
    # колонтитулы «Книга инженера по растворам ЗАО «ССК»  7»
    t = re.sub(r"^\s*\d*\s*Книга инженера по растворам ЗАО «ССК»\s*\d*\s*$", "", t, flags=re.M)
    # перенос: «обесD\n   печивать»
    t = re.sub(rf"([{CYR}])D[ \t]*\n[ \t]*([{CYR}a-z])", r"\1\2", t)
    t = re.sub(rf"([{CYR}])‐[ \t]*\n[ \t]*([а-яё])", r"\1\2", t)
    # степени: 10D6 -> 10^-6
    t = re.sub(r"(?<![\d\-])10D(\d{1,2})(?![\dD])", r"10^-\1", t)
    # D между кириллицей/цифрами -> дефис/минус
    t = re.sub(rf"(?<=[{CYR}0-9)])D(?=[{CYR}0-9(])", "-", t)
    t = re.sub(rf"(?<=[{CYR}0-9])D(?=[\s.,;:)])", "-", t)      # СО32D, ионы S 2D
    t = re.sub(rf"(?<=[\s(=])D(?=[{CYR}])", "-", t)            # «Dлг», « Dвид»
    t = re.sub(rf"(?<=[{CYR}])D$", "-", t, flags=re.M)
    t = t.replace("‐", "-")
    # другие артефакты дефиса/минуса: «!», «&», «%», «A» между символами
    t = re.sub(rf"(?<=[{CYR}A-Za-z0-9])!(?=[{CYR}A-Za-z0-9(])", "-", t)   # УБТ!Р!73, 10!24
    t = re.sub(rf"(?<=[0-9])!(?=[\s)])", "-", t)                            # заряды «1!»
    t = re.sub(rf"(?<=[{CYR}])&(?=\s|$)", "-", t, flags=re.M)              # «Относитель&» в таблицах
    t = re.sub(rf"(?<=[{CYR}A-Za-z])%(?=[{CYR}A-Za-z0-9])", "-", t)          # ОП%10, УНБ%600
    t = re.sub(rf"(?<=[{CYR}0-9%])A(?=[{CYR}0-9])", "-", t)                  # сAрасстояние, 2%Aная, минA1
    # убрать общий отступ и лишние пустые строки
    lines = [l.rstrip() for l in t.split("\n")]
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    lines = [l[ind:] for l in lines]
    t = "\n".join(lines)
    t = re.sub(r"\n{3,}", "\n\n", t).strip("\n")
    return t

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True).stdout
    pages = raw.split("\f")
    n = 0
    for i, p in enumerate(pages, 1):
        if i > 543 and not p.strip():
            continue
        (OUT / f"стр{i:03d}.txt").write_text(clean(p) + "\n", encoding="utf-8")
        n += 1
    print(f"{n} страниц -> {OUT}")

if __name__ == "__main__":
    main()

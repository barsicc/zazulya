"""Схема АБР-1 по лекциям (с. 109 PDF) и рис. 1 в рекомендациях Блинова."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "svg.hashsalt": "abr-1-schematic",
    })
    figure = plt.figure(figsize=(6.15, 3.24))
    axes = figure.add_axes((0, 0, 1, 1))
    axes.set(xlim=(0, 800), ylim=(422, 0), aspect="equal")
    axes.set_axis_off()

    water_level = 129
    axes.add_patch(Rectangle((245, water_level), 306, 242, facecolor="0.92", edgecolor="none"))
    axes.plot([245, 245, 551, 551], [108, 371, 371, 108], color="black", linewidth=1.35)
    axes.hlines(water_level, 245, 551, colors="black", linewidth=1.05)

    # Стакан под поплавком, груз установлен на нижнем конце прибора.
    axes.add_patch(Rectangle((383, 34), 46, 170, facecolor="white", edgecolor="black", zorder=3))
    axes.add_patch(Polygon([(383, 190), (429, 190), (450, 212), (450, 257),
                            (362, 257), (362, 212)], closed=True,
                           facecolor="white", edgecolor="black", zorder=3))
    axes.add_patch(Rectangle((365, 257), 82, 70, facecolor="white", edgecolor="black", zorder=3))
    axes.add_patch(Rectangle((371, 266), 70, 45, facecolor="0.78", edgecolor="none", zorder=4))
    axes.add_patch(Rectangle((382, 327), 48, 23, facecolor="0.45", edgecolor="black", zorder=4))

    # Риски отмечают место отсчёта. Развёртка шкал зависит от исполнения прибора.
    for mark in range(54, 181, 15):
        length = 25 if mark == water_level else 15
        axes.hlines(mark, 383, 383 + length, colors="black", linewidth=0.85, zorder=5)

    axes.plot([207, 245], [water_level, water_level], color="black", linewidth=0.7)
    axes.plot([207, 278], [240, 240], color="black", linewidth=0.7)
    axes.text(18, water_level, "Уровень отсчёта", va="center")
    axes.text(18, 240, "Ведёрко с водой", va="center")

    axes.plot([429, 568], [67, 67], color="black", linewidth=0.7)
    axes.text(579, 67, "Стержень\nОсновная и\nпоправочная шкалы", va="center")
    for start, height, label in ((450, 226, "Поплавок"),
                                 (447, 289, "Мерный стакан\nс пробой"),
                                 (430, 338, "Съёмный груз")):
        axes.plot([start, 568], [height, height], color="black", linewidth=0.7)
        axes.text(579, height, label, va="center")
    axes.text(400, 402, "Условные очертания и риски шкал", fontsize=9, ha="center", va="center")

    output = Path(__file__).resolve().parents[1] / "иллюстрации"
    figure.savefig(output / "АБР-1.png", dpi=300)
    vector = output / "АБР-1.svg"
    figure.savefig(vector, metadata={"Date": None})
    lines = vector.read_text(encoding="utf-8").splitlines()
    vector.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
    plt.close(figure)


if __name__ == "__main__":
    main()

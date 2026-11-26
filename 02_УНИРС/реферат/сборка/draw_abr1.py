"""Условная схема АБР-1 по описанию на с. 109–110 PDF лекций.

Запуск из корня репозитория:
python3 -B 02_УНИРС/реферат/сборка/draw_abr1.py

Требуется Matplotlib.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse, Rectangle


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "svg.hashsalt": "abr-1-schematic",
    })
    figure = plt.figure(figsize=(6.15, 3.05))
    axes = figure.add_axes((0, 0, 1, 1))
    axes.set(xlim=(0, 800), ylim=(396, 0), aspect="equal")
    axes.set_axis_off()

    # Условные очертания ванны, поплавка со стержнем и стакана.
    water_level = 172
    axes.add_patch(Rectangle((198, water_level), 355, 184, facecolor="0.92", edgecolor="none"))
    axes.plot([198, 198, 553, 553], [149, 356, 356, 149], color="black", linewidth=1.3)
    axes.plot([198, 553], [water_level, water_level], color="black", linewidth=1.15)
    axes.add_patch(Ellipse((378, 227), 134, 76, facecolor="white", edgecolor="black", linewidth=1.3,
                           zorder=3))
    axes.add_patch(Rectangle((351, 42), 54, 157, facecolor="white", edgecolor="black", linewidth=1.3,
                             zorder=4))
    axes.add_patch(Rectangle((335, 254), 86, 70, facecolor="white", edgecolor="black", linewidth=1.3,
                             zorder=4))
    axes.add_patch(Rectangle((341, 260), 74, 58, facecolor="0.68", edgecolor="none", zorder=5))

    # Риски передают положение двух шкал без условных числовых показаний.
    axes.vlines(378, 53, 192, colors="0.72", linewidth=0.55, zorder=5)
    for mark in range(60, 187, 14):
        length = 17 if mark in (88, 130, water_level) else 10
        axes.hlines(mark, 351, 351 + length, colors="black", linewidth=0.85, zorder=6)
        axes.hlines(mark, 405 - length, 405, colors="black", linewidth=0.85, zorder=6)
    axes.hlines(water_level, 368, 388, colors="0.35", linestyles="dotted", linewidth=0.75, zorder=6)

    # Источник перечисляет съёмный груз без положения и формы.
    axes.add_patch(Rectangle((627, 138), 55, 21, facecolor="0.68", edgecolor="black", linewidth=1.15))
    axes.text(654.5, 179, "Съёмный груз", ha="center", va="center")

    # Выносные линии подписей.
    axes.plot([196, 351], [88, 88], color="black", linewidth=0.75, zorder=6)
    axes.plot([405, 551], [88, 88], color="black", linewidth=0.75, zorder=6)
    axes.plot([124, 198], [water_level, water_level], color="black", linewidth=0.75, zorder=6)
    axes.plot([78, 166, 235], [251, 251, 226], color="black", linewidth=0.75, zorder=6)
    axes.plot([445, 561], [227, 227], color="black", linewidth=0.75, zorder=6)
    axes.plot([421, 561], [289, 289], color="black", linewidth=0.75, zorder=6)
    axes.text(22, 88, "Основная шкала\nг/см³", va="center")
    axes.text(563, 88, "Поправочная шкала\nг/см³", va="center")
    axes.text(22, water_level, "Уровень\nотсчёта", va="center")
    axes.text(22, 251, "Вода", va="center")
    axes.text(573, 227, "Поплавок\nсо стержнем", va="center")
    axes.text(573, 289, "Мерный стакан\nс пробой", va="center")
    axes.text(375.5, 379, "Схема условная", fontsize=9, ha="center", va="center")

    output = Path(__file__).resolve().parents[1] / "иллюстрации"
    figure.savefig(output / "АБР-1.png", dpi=300)
    vector = output / "АБР-1.svg"
    figure.savefig(vector, metadata={"Date": None})
    lines = vector.read_text(encoding="utf-8").splitlines()
    vector.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
    plt.close(figure)


if __name__ == "__main__":
    main()

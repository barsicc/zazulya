"""График разбавления для задания № 3.

Запуск из корня репозитория:
python3 -B 02_УНИРС/реферат/сборка/plot_dilution.py --report

Без аргументов строится прежний проверочный PDF. Для реферата
ключ --report записывает PNG и SVG. Требуется Matplotlib.
"""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

REPORT = Path(__file__).resolve().parents[1]
CALCULATIONS = REPORT.parent / "расчеты"
sys.path.insert(0, str(CALCULATIONS))
from calculate_variant_07 import added_volume


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="Сохранить рисунок для реферата")
    arguments = parser.parse_args()

    registry = json.loads((CALCULATIONS / "RESULTS.json").read_text(encoding="utf-8"))
    inputs = registry["inputs"]["dilution"]
    results = registry["results"]["dilution"]
    initial_volume = Fraction(inputs["initial_volume"])
    reduction = Fraction(inputs["density_reduction"])
    scenario_density = Fraction(inputs["initial_density"])

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "pdf.fonttype": 42,
        "svg.hashsalt": "variant-07-dilution",
    })
    figure, axes = plt.subplots(figsize=(6.15, 3.5), layout="constrained")
    boundaries = []
    series = (("water", "Пресная вода", "-", "o"), ("oil", "Нефть", "--", "s"))
    for key, label, line_style, marker in series:
        density = Fraction(inputs[f"{key}_density"])
        boundary = reduction + density
        boundaries.append(boundary)
        densities = [start for start in range(1300, 2201, 5) if start > boundary]
        volumes = [added_volume(initial_volume, start, start - reduction, density) for start in densities]
        curve, = axes.plot(densities, [float(volume) for volume in volumes], line_style,
                           color="black", linewidth=1.35, label=label)

        scenario_volume = added_volume(initial_volume, scenario_density, scenario_density - reduction, density)
        registered_volume = results[key]["added_volume"]
        if scenario_volume != Fraction(registered_volume["exact"]):
            raise ValueError(f"Точка сценария для {label} расходится с реестром")
        if arguments.report:
            curve.set_marker(marker)
            curve.set_markerfacecolor("white")
            curve.set_markersize(5)
            curve.set_markevery([])
        axes.plot(float(scenario_density), float(scenario_volume), marker,
                  color="black", markerfacecolor="white", markersize=5, zorder=4)
        offset = {"water": 6, "oil": -12 if arguments.report else -7}[key]
        axes.annotate(registered_volume["rounded"].replace(".", ","),
                      (float(scenario_density), float(scenario_volume)), xytext=(8, offset),
                      textcoords="offset points", va="center", fontsize=9)

    axes.axvline(float(scenario_density), color="0.55", linestyle=":", linewidth=0.9)
    axes.set(xlim=(1300, 2200), ylim=(0, None),
             xlabel="Начальная плотность раствора ρ₀, кг/м³",
             ylabel="Объём разбавителя, м³")
    axes.xaxis.set_major_locator(MultipleLocator(100))
    axes.yaxis.set_major_locator(MultipleLocator(100))
    axes.set_axisbelow(True)
    axes.grid(color="0.87", linewidth=0.55)
    axes.legend(frameon=False)
    axes.spines[["top", "right"]].set_visible(False)
    output = REPORT / "иллюстрации"
    if arguments.report:
        figure.savefig(output / "РАЗБАВЛЕНИЕ.png", dpi=300)
        vector = output / "РАЗБАВЛЕНИЕ.svg"
        figure.savefig(vector, metadata={"Date": None})
        lines = vector.read_text(encoding="utf-8").splitlines()
        vector.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
    else:
        axes.set_title(
            f"Начальный объём {initial_volume} м³, снижение плотности {reduction} кг/м³",
            fontsize=10,
        )
        figure.supxlabel(
            f"Границы достижимости (вне графика): ρ₀ > {boundaries[0]} кг/м³ для воды,\n"
            f"ρ₀ > {boundaries[1]} кг/м³ для нефти.",
            fontsize=8,
        )
        figure.savefig(
            output / "РАЗБАВЛЕНИЕ_ПРОВЕРКА.pdf",
            metadata={"Title": "Проверочный график разбавления", "CreationDate": None},
        )
    plt.close(figure)


if __name__ == "__main__":
    main()

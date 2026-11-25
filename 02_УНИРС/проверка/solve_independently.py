#!/usr/bin/env python3
"""Решение варианта № 7 методом Гаусса — Жордана в точных дробях."""

import argparse
import json
from fractions import Fraction
from pathlib import Path


def exact_inputs(section, *keys):
    values = []
    for key in keys:
        value = section[key]
        if type(value) not in (int, str):
            raise ValueError(f"Поле {key} должно быть целым числом или строкой дроби")
        values.append(Fraction(value))
    return values


def solve_linear(rows):
    matrix = [[Fraction(entry) for entry in row] for row in rows]
    size = len(matrix)
    for column in range(size):
        pivot = next((i for i in range(column, size) if matrix[i][column]), None)
        if pivot is None:
            raise ValueError("Система баланса вырождена")
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]

        divisor = matrix[column][column]
        pivot_row = [entry / divisor for entry in matrix[column]]
        matrix[column] = pivot_row
        for i, row in enumerate(matrix):
            if i != column and row[column]:
                factor = row[column]
                matrix[i] = [a - factor * b for a, b in zip(row, pivot_row)]

    return [row[-1] for row in matrix]


def solve_addition(initial_volume, initial_density, target_density, added_density):
    if min(initial_volume, initial_density, target_density, added_density) <= 0:
        raise ValueError("Объём и плотности должны быть положительными")
    if not min(initial_density, added_density) < target_density < max(initial_density, added_density):
        raise ValueError(
            f"Плотность {target_density} недостижима конечной положительной добавкой "
            f"плотностью {added_density} к раствору плотностью {initial_density}"
        )

    initial_mass = initial_volume * initial_density
    # Порядок неизвестных: объём добавки, итоговый объём, масса добавки, итоговая масса.
    added_volume, final_volume, added_mass, final_mass = solve_linear([
        [0, 0, -1, 1, initial_mass],
        [-1, 1, 0, 0, initial_volume],
        [-added_density, 0, 1, 0, 0],
        [0, -target_density, 0, 1, 0],
    ])
    final_density = final_mass / final_volume
    if (
        added_volume <= 0
        or added_mass <= 0
        or final_volume - added_volume != initial_volume
        or final_mass - added_mass != initial_mass
        or added_mass / added_volume != added_density
        or final_density != target_density
    ):
        raise ArithmeticError("Результат не прошёл проверку баланса добавления")

    return {
        "added_volume": added_volume,
        "final_volume": final_volume,
        "added_mass": added_mass,
        "final_mass": final_mass,
        "final_density": final_density,
    }


def solve_weighting(section):
    volume, initial, target, iron_density, barite_density = exact_inputs(
        section, "initial_volume", "initial_density", "target_density",
        "iron_oxide_density", "barite_density",
    )
    if target <= initial:
        raise ValueError("При утяжелении плотность должна возрастать")

    iron = solve_addition(volume, initial, target, iron_density)
    barite = solve_addition(volume, initial, target, barite_density)
    mass_difference = barite["added_mass"] - iron["added_mass"]
    volume_difference = barite["added_volume"] - iron["added_volume"]
    return {
        "iron_oxide": iron,
        "barite": barite,
        "initial_mass": initial * volume,
        "mass_difference": mass_difference,
        "mass_saving_percent": 100 * mass_difference / barite["added_mass"],
        "volume_difference": volume_difference,
        "volume_saving_percent": 100 * volume_difference / barite["added_volume"],
    }


def solve_bentonite(section):
    mass, mass_fraction, bentonite_density, water_density = exact_inputs(
        section, "basis_mass", "bentonite_mass_fraction", "bentonite_density", "water_density",
    )
    if min(mass, bentonite_density, water_density) <= 0 or not 0 <= mass_fraction <= 1:
        raise ValueError("Масса и плотности должны быть положительными, массовая доля — от 0 до 1")

    # Порядок неизвестных: объёмы бентонита, воды и готовой смеси.
    bentonite_volume, water_volume, final_volume = solve_linear([
        [bentonite_density, water_density, 0, mass],
        [bentonite_density, 0, 0, mass * mass_fraction],
        [-1, -1, 1, 0],
    ])
    bentonite_mass = bentonite_density * bentonite_volume
    water_mass = water_density * water_volume
    final_density = mass / final_volume
    if (
        min(bentonite_volume, water_volume) < 0
        or bentonite_mass + water_mass != mass
        or bentonite_mass / mass != mass_fraction
        or bentonite_volume + water_volume != final_volume
        or not min(bentonite_density, water_density) <= final_density <= max(bentonite_density, water_density)
    ):
        raise ArithmeticError("Результат не прошёл проверку баланса смеси бентонита с водой")

    return {
        "bentonite_mass": bentonite_mass,
        "water_mass": water_mass,
        "bentonite_volume": bentonite_volume,
        "water_volume": water_volume,
        "final_volume": final_volume,
        "final_density": final_density,
        "bentonite_volume_percent": 100 * bentonite_volume / final_volume,
    }


def solve_dilution(section):
    volume, initial, reduction, oil_fraction, water_density, oil_density = exact_inputs(
        section, "initial_volume", "initial_density", "density_reduction",
        "initial_oil_volume_fraction", "water_density", "oil_density",
    )
    if reduction <= 0 or not 0 <= oil_fraction <= 1:
        raise ValueError("Снижение должно быть положительным, исходная объёмная доля нефти — от 0 до 1")
    oil_contribution = oil_density * oil_fraction
    if (oil_fraction == 1 and initial != oil_density) or (oil_fraction < 1 and initial <= oil_contribution):
        raise ValueError("Исходные плотность и объёмная доля нефти физически несовместимы")

    target = initial - reduction
    water = solve_addition(volume, initial, target, water_density)
    oil = solve_addition(volume, initial, target, oil_density)
    initial_oil_volume = volume * oil_fraction
    water["final_oil_volume_percent"] = 100 * initial_oil_volume / water["final_volume"]
    oil["final_oil_volume_percent"] = 100 * (initial_oil_volume + oil["added_volume"]) / oil["final_volume"]
    volume_difference = water["added_volume"] - oil["added_volume"]
    return {
        "water": water,
        "oil": oil,
        "initial_mass": initial * volume,
        "target_density": target,
        "volume_difference": volume_difference,
        "volume_saving_percent": 100 * volume_difference / water["added_volume"],
    }


def main():
    default_input = Path(__file__).resolve().parents[1] / "задания" / "ВАРИАНТ_07.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path, nargs="?", default=default_input)
    args = parser.parse_args()

    try:
        variant = json.loads(args.input_path.read_text(encoding="utf-8"))
        results = {
            "weighting": solve_weighting(variant["weighting"]),
            "bentonite": solve_bentonite(variant["bentonite"]),
            "dilution": solve_dilution(variant["dilution"]),
        }
    except (OSError, KeyError, ValueError, ZeroDivisionError) as error:
        parser.exit(2, f"{error}\n")

    print(json.dumps(results, default=str, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

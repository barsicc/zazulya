"""Точный расчёт варианта 7 для модели с аддитивными объёмами."""

import argparse
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path


DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "задания" / "ВАРИАНТ_07.json"


class UnreachableDensity(ValueError):
    """Конечный объём добавки с заданной плотностью не существует."""


def exact_number(value, name):
    if not isinstance(value, (str, int, Decimal, Fraction)) or isinstance(value, bool):
        raise ValueError(f"{name}: требуется точное число.")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError(f"{name}: некорректное число.") from exc


def positive(value, name):
    number = exact_number(value, name)
    if number <= 0:
        raise ValueError(f"{name}: величина должна быть положительной.")
    return number


def unit_fraction(value, name):
    number = exact_number(value, name)
    if not 0 <= number <= 1:
        raise ValueError(f"{name}: доля должна находиться в пределах от 0 до 1.")
    return number


def added_volume(initial_volume, initial_density, target_density, added_density):
    volume = positive(initial_volume, "initial_volume")
    start = positive(initial_density, "initial_density")
    target = positive(target_density, "target_density")
    addition = positive(added_density, "added_density")
    if target == start:
        return Fraction(0)
    if target == addition:
        raise UnreachableDensity("Цель равна плотности добавки и достигается лишь в пределе.")
    if not min(start, addition) < target < max(start, addition):
        raise UnreachableDensity("Цель лежит вне интервала между плотностями исходного раствора и добавки.")
    return volume * (target - start) / (addition - target)


def mixture_density(initial_volume, initial_density, add_volume, added_density):
    total_mass = initial_volume * initial_density + add_volume * added_density
    return Fraction(total_mass, initial_volume + add_volume)


def rounding(value, places):
    """Округлить рациональное число без промежуточной десятичной аппроксимации."""
    scale = 10 ** places
    units, remainder = divmod(abs(value.numerator) * scale, value.denominator)
    if 2 * remainder >= value.denominator:
        units += 1
    integer, decimal = divmod(units, scale)
    sign = "-" if value < 0 and units else ""
    return f"{sign}{integer}.{decimal:0{places}d}"


def quantity(value, unit, places=2):
    exact = Fraction(value)
    return {"exact": str(exact), "unit": unit, "rounded": rounding(exact, places)}


def verification(**checks):
    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise ArithmeticError(f"Невязка при обратной проверке: {failed}")
    return {name: "passed" for name in checks}


def addition_scenario(volume, start, target, density):
    density = positive(density, "added_density")
    try:
        increment = added_volume(volume, start, target, density)
    except UnreachableDensity as exc:
        return {"status": "unreachable", "reason": str(exc), "checks": None}

    initial_mass = volume * start
    added_mass = increment * density
    final_mass = initial_mass + added_mass
    final_volume = volume + increment
    achieved = mixture_density(volume, start, increment, density)
    checks = verification(
        mass_balance=target * final_volume == initial_mass + added_mass,
        volume_balance=final_mass / target == volume + added_mass / density,
        target_density=achieved == target,
    )
    return {
        "status": "no_change" if increment == 0 else "calculated",
        "added_volume": quantity(increment, "м³"),
        "added_mass": quantity(added_mass, "кг"),
        "final_volume": quantity(final_volume, "м³"),
        "final_mass": quantity(final_mass, "кг"),
        "achieved_density": quantity(achieved, "кг/м³"),
        "checks": checks,
    }


def comparison(reference, alternative, key, unit, basis):
    if "unreachable" in (reference["status"], alternative["status"]):
        return None
    baseline = Fraction(reference[key]["exact"])
    difference = baseline - Fraction(alternative[key]["exact"])
    return {
        "difference": quantity(difference, unit),
        "reduction_percent": quantity(100 * difference / baseline, "%") if baseline else None,
        "reference": basis,
    }


def solve_weighting(data):
    volume = positive(data["initial_volume"], "weighting.initial_volume")
    start = positive(data["initial_density"], "weighting.initial_density")
    target = positive(data["target_density"], "weighting.target_density")
    if target < start:
        raise ValueError("weighting.target_density: цель утяжеления ниже исходной плотности.")
    iron_oxide = addition_scenario(volume, start, target, data["iron_oxide_density"])
    barite = addition_scenario(volume, start, target, data["barite_density"])
    return {
        "initial_mass": quantity(volume * start, "кг"),
        "iron_oxide": iron_oxide,
        "barite": barite,
        "mass_comparison": comparison(barite, iron_oxide, "added_mass", "кг", "barite"),
        "volume_comparison": comparison(barite, iron_oxide, "added_volume", "м³", "barite"),
    }


def solve_bentonite(data):
    mass = positive(data["basis_mass"], "bentonite.basis_mass")
    fraction = unit_fraction(data["bentonite_mass_fraction"], "bentonite.bentonite_mass_fraction")
    bentonite_density = positive(data["bentonite_density"], "bentonite.bentonite_density")
    water_density = positive(data["water_density"], "bentonite.water_density")

    bentonite_mass = mass * fraction
    water_mass = mass - bentonite_mass
    bentonite_volume = bentonite_mass / bentonite_density
    water_volume = water_mass / water_density
    total_volume = water_volume + bentonite_volume
    mixture = mass / total_volume
    bentonite_share = bentonite_volume / total_volume
    checks = verification(
        mass_balance=water_volume * water_density + bentonite_volume * bentonite_density == mass,
        volume_balance=mass / mixture == water_mass / water_density + bentonite_mass / bentonite_density,
        fraction_balance=water_volume / total_volume + bentonite_share == 1,
        density=mixture == (1 - bentonite_share) * water_density + bentonite_share * bentonite_density,
    )
    return {
        "water_mass": quantity(water_mass, "кг"),
        "bentonite_mass": quantity(bentonite_mass, "кг"),
        "water_volume": quantity(water_volume, "м³", places=4),
        "bentonite_volume": quantity(bentonite_volume, "м³", places=4),
        "total_volume": quantity(total_volume, "м³", places=4),
        "mixture_density": quantity(mixture, "кг/м³"),
        "bentonite_volume_percent": quantity(100 * bentonite_share, "% об."),
        "checks": checks,
    }


def oil_content(scenario, initial_oil, addition_is_oil):
    if scenario["status"] == "unreachable":
        return
    added_oil = Fraction(scenario["added_volume"]["exact"]) if addition_is_oil else Fraction(0)
    oil = initial_oil + added_oil
    final_volume = Fraction(scenario["final_volume"]["exact"])
    share = oil / final_volume
    scenario["final_oil_volume_percent"] = quantity(100 * share, "% об.")
    scenario["checks"].update(verification(
        oil_volume_balance=0 <= oil <= final_volume and share * final_volume - added_oil == initial_oil,
    ))


def solve_dilution(data):
    volume = positive(data["initial_volume"], "dilution.initial_volume")
    start = positive(data["initial_density"], "dilution.initial_density")
    reduction = exact_number(data["density_reduction"], "dilution.density_reduction")
    if not 0 <= reduction < start:
        raise ValueError("dilution.density_reduction: требуется снижение от нуля до исходной плотности, верхняя граница исключается.")
    target = start - reduction
    oil_fraction = unit_fraction(data["initial_oil_volume_fraction"], "dilution.initial_oil_volume_fraction")
    oil_density = positive(data["oil_density"], "dilution.oil_density")
    # Исходная нефть и добавляемая нефть считаются одной фазой.
    oil_mass_per_volume = oil_fraction * oil_density
    if (oil_fraction == 1 and start != oil_density) or (oil_fraction < 1 and start <= oil_mass_per_volume):
        raise ValueError("dilution.initial_oil_volume_fraction: доля нефти несовместима с исходной плотностью.")
    water = addition_scenario(volume, start, target, data["water_density"])
    oil = addition_scenario(volume, start, target, oil_density)
    oil_content(water, volume * oil_fraction, addition_is_oil=False)
    oil_content(oil, volume * oil_fraction, addition_is_oil=True)
    return {
        "initial_mass": quantity(volume * start, "кг"),
        "target_density": quantity(target, "кг/м³"),
        "water": water,
        "oil": oil,
        "volume_comparison": comparison(water, oil, "added_volume", "м³", "water"),
    }


def calculate(data):
    return {
        "schema_version": 1,
        "inputs": data,
        "rounding": {
            "method": "До ближайшего значения, при равенстве — от нуля. Округляются только поля rounded.",
            "places_default": 2,
            "places_bentonite_volumes": 4,
            "exact": "Строка целого числа или несократимой обыкновенной дроби в указанной единице.",
        },
        "results": {
            "weighting": solve_weighting(data["weighting"]),
            "bentonite": solve_bentonite(data["bentonite"]),
            "dilution": solve_dilution(data["dilution"]),
        },
    }


def json_number(value):
    """Сохранить точность десятичных литералов из пользовательского JSON."""
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Неподдерживаемый тип: {type(value).__name__}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="файл исходных данных")
    parser.add_argument("--output", type=Path, help="файл результатов (по умолчанию stdout)")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"), parse_float=Decimal)
        result = json.dumps(calculate(data), ensure_ascii=False, indent=2, default=json_number) + "\n"
        if args.output is None:
            print(result, end="")
        else:
            args.output.write_text(result, encoding="utf-8")
    except (ArithmeticError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Ошибка расчёта: {exc}\n")


if __name__ == "__main__":
    main()

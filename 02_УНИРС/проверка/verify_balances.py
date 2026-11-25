"""Контроль учебных расчётов варианта 7 в единицах СИ."""

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import importlib
import json
from math import ceil
import unittest


# Импорт из соседнего каталога при прямом запуске этого файла.
if not __package__:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

calculation = importlib.import_module("расчеты.calculate_variant_07")
independent = importlib.import_module("проверка.solve_independently")
added_volume = calculation.added_volume
mixture_density = calculation.mixture_density


class BalanceTests(unittest.TestCase):
    def check_change(self, initial_volume, initial_density, target_density, density):
        volume = added_volume(initial_volume, initial_density, target_density, density)
        self.assertGreater(volume, 0)
        self.assertEqual(
            mixture_density(initial_volume, initial_density, volume, density),
            target_density,
        )
        return volume

    def test_barite_example_1(self):
        volume = self.check_change(10, 1500, 2000, 4250)
        self.assertEqual(volume, Fraction(20, 9))
        mass = volume * 4250
        self.assertEqual(mass, Fraction(85000, 9))
        self.assertEqual(ceil(mass / Fraction("42.64")), 222)

    def test_weighting_variant_7(self):
        oxide_volume = self.check_change(100, 1350, 1600, 4700)
        barite_volume = self.check_change(100, 1350, 1600, 4250)
        self.assertEqual(oxide_volume, Fraction(250, 31))
        self.assertEqual(barite_volume, Fraction(500, 53))
        oxide_mass = oxide_volume * 4700
        barite_mass = barite_volume * 4250
        self.assertEqual(oxide_mass, Fraction(1175000, 31))
        self.assertEqual(barite_mass, Fraction(2125000, 53))
        self.assertEqual(barite_mass - oxide_mass, Fraction(3600000, 1643))

    def test_bentonite_mass_fractions(self):
        for bentonite_mass, expected_density, expected_fraction in [
            (5, Fraction(100000, 97), Fraction(2, 97)),
            (7, Fraction(500000, 479), Fraction(14, 479)),
        ]:
            with self.subTest(bentonite_percent=bentonite_mass):
                w = Fraction(bentonite_mass, 100)
                volume = Fraction(100 - bentonite_mass, 1000)
                bentonite_volume = Fraction(bentonite_mass, 2500)
                density = 1 / ((1 - w) / 1000 + w / 2500)
                self.assertEqual(density, expected_density)
                self.assertEqual(bentonite_volume / (volume + bentonite_volume), expected_fraction)
                self.assertEqual(
                    mixture_density(volume, 1000, bentonite_volume, 2500),
                    density,
                )

    def test_dilution_example_3(self):
        water = self.check_change(100, 3000, 2700, 1000)
        oil = self.check_change(100, 3000, 2700, 823)
        self.assertEqual(water, Fraction(300, 17))
        self.assertEqual(oil, Fraction(30000, 1877))
        self.assertEqual(100 * oil / (100 + oil), Fraction(30000, 2177))

    def test_dilution_variant_7_two_starting_densities(self):
        cases = [
            (1600, 100, Fraction(1600, 23), Fraction(800, 31)),
            (1500, Fraction(400, 3), Fraction(1600, 19), Fraction(800, 27)),
        ]
        for start, expected_water, expected_oil, expected_percent in cases:
            with self.subTest(initial_density=start):
                water = self.check_change(200, start, start - 200, 1000)
                oil = self.check_change(200, start, start - 200, 825)
                self.assertEqual(water, expected_water)
                self.assertEqual(oil, expected_oil)
                self.assertEqual(100 * oil / (200 + oil), expected_percent)
                self.assertEqual(Fraction(20000, start - 825), expected_percent)

    def test_fixed_final_volume_example_25(self):
        final_volume = Fraction(1, 1000)
        volume = final_volume * Fraction(1250 - 1040, 4250 - 1040)
        self.assertEqual(volume * 4250, Fraction(119, 428))
        self.assertEqual(mixture_density(final_volume - volume, 1040, volume, 4250), 1250)

    def test_dilution_lecture_example_5(self):
        result = self.check_change(159, 1920, 1440, 1000)
        self.assertEqual(result, Fraction(1908, 11))


class VariantInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads(calculation.DEFAULT_INPUT.read_text(encoding="utf-8"))

    def setUp(self):
        self.data = deepcopy(self.inputs)

    def solve_dilution(self):
        return calculation.calculate(self.data)["results"]["dilution"]

    def test_no_change_requires_no_addition(self):
        self.data["dilution"]["density_reduction"] = 0
        self.data["dilution"]["initial_oil_volume_fraction"] = "1/10"
        dilution = self.solve_dilution()
        for name in ("water", "oil"):
            with self.subTest(addition=name):
                result = dilution[name]
                self.assertEqual(result["status"], "no_change")
                self.assertEqual(result["added_volume"]["exact"], "0")
                self.assertEqual(result["final_oil_volume_percent"]["exact"], "10")
        self.assertIsNone(dilution["volume_comparison"]["reduction_percent"])
        self.assertEqual(added_volume(200, 1000, 1000, 1000), 0)

    def test_unreachable_target_preserves_feasible_alternative(self):
        self.data["dilution"]["initial_density"] = 1150
        dilution = self.solve_dilution()
        self.assertEqual(dilution["water"]["status"], "unreachable")
        self.assertEqual(dilution["oil"]["status"], "calculated")
        self.assertEqual(dilution["oil"]["achieved_density"]["exact"], "950")
        self.assertIsNone(dilution["volume_comparison"])
        with self.assertRaises(calculation.UnreachableDensity):
            added_volume(100, 1350, 4900, 4700)

    def test_target_equal_to_density_of_addition(self):
        with self.assertRaisesRegex(calculation.UnreachableDensity, "равна плотности"):
            added_volume(200, 1200, 1000, 1000)

    def test_invalid_mass_and_volume_fractions(self):
        keys = {
            "bentonite": "bentonite_mass_fraction",
            "dilution": "initial_oil_volume_fraction",
        }
        for task, field in keys.items():
            for invalid in ("-1/10", "11/10", True, "1/0"):
                with self.subTest(field=field, value=invalid):
                    data = deepcopy(self.data)
                    data[task][field] = invalid
                    with self.assertRaisesRegex(ValueError, field):
                        calculation.calculate(data)

    def test_negative_and_zero_initial_volumes(self):
        for task in ("weighting", "dilution"):
            for invalid in (-1, 0):
                with self.subTest(task=task, volume=invalid):
                    data = deepcopy(self.data)
                    data[task]["initial_volume"] = invalid
                    with self.assertRaisesRegex(ValueError, "initial_volume"):
                        calculation.calculate(data)

    def test_existing_oil_is_included_for_both_alternatives(self):
        self.data["dilution"]["initial_oil_volume_fraction"] = "1/10"
        dilution = self.solve_dilution()
        self.assertEqual(dilution["water"]["final_oil_volume_percent"]["exact"], "20/3")
        self.assertEqual(dilution["oil"]["final_oil_volume_percent"]["exact"], "1030/31")
        self.assertEqual(dilution["water"]["checks"]["oil_volume_balance"], "passed")
        self.assertEqual(dilution["oil"]["checks"]["oil_volume_balance"], "passed")

    def test_changed_initial_density_and_exact_decimal_inputs(self):
        self.data["dilution"]["initial_density"] = "1500"
        self.data["dilution"]["oil_density"] = Decimal("825.0")
        dilution = self.solve_dilution()
        self.assertEqual(dilution["target_density"]["exact"], "1300")
        self.assertEqual(dilution["water"]["added_volume"]["exact"], "400/3")
        self.assertEqual(dilution["oil"]["added_volume"]["exact"], "1600/19")

    def test_invalid_density_and_density_reduction(self):
        for field, value in [("oil_density", -825), ("density_reduction", 1600), ("density_reduction", -1)]:
            with self.subTest(field=field, value=value):
                data = deepcopy(self.data)
                data["dilution"][field] = value
                with self.assertRaises(ValueError):
                    calculation.calculate(data)

    def test_incompatible_oil_content_and_initial_density(self):
        self.data["dilution"]["initial_oil_volume_fraction"] = 1
        with self.assertRaisesRegex(ValueError, "initial_oil_volume_fraction"):
            self.solve_dilution()

    def test_registry_matches_recalculation(self):
        path = calculation.DEFAULT_INPUT.parent.parent / "расчеты" / "RESULTS.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(calculation.calculate(self.data), expected)

    def test_all_exact_results_match_independent_solver(self):
        actual = calculation.calculate(self.data)["results"]
        expected = {
            "weighting": independent.solve_weighting(self.data["weighting"]),
            "bentonite": independent.solve_bentonite(self.data["bentonite"]),
            "dilution": independent.solve_dilution(self.data["dilution"]),
        }
        aliases = {
            "achieved_density": "final_density",
            "total_volume": "final_volume",
            "mixture_density": "final_density",
        }

        def flatten_results(values):
            exact = {}
            for key, value in values.items():
                if not isinstance(value, dict) or key == "checks":
                    continue
                if "exact" in value:
                    exact[aliases.get(key, key)] = Fraction(value["exact"])
                elif key.endswith("_comparison"):
                    prefix = key.removesuffix("_comparison")
                    exact[f"{prefix}_difference"] = Fraction(value["difference"]["exact"])
                    exact[f"{prefix}_saving_percent"] = Fraction(value["reduction_percent"]["exact"])
                else:
                    exact[key] = flatten_results(value)
            return exact

        self.assertEqual(flatten_results(actual), expected)

    def test_rounding_of_exact_halves(self):
        self.assertEqual(calculation.rounding(Fraction(201, 200), 2), "1.01")
        self.assertEqual(calculation.rounding(Fraction(-201, 200), 2), "-1.01")


if __name__ == "__main__":
    unittest.main()

"""Контроль учебных расчётов варианта 7 в единицах СИ."""

from fractions import Fraction
from math import ceil
import unittest


def added_volume(initial_volume, initial_density, target_density, added_density):
    return initial_volume * Fraction(
        target_density - initial_density, added_density - target_density
    )


def mixture_density(initial_volume, initial_density, add_volume, added_density):
    total_mass = initial_volume * initial_density + add_volume * added_density
    return Fraction(total_mass, initial_volume + add_volume)


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


if __name__ == "__main__":
    unittest.main()

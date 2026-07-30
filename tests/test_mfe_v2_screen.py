from __future__ import annotations

import csv
import unittest
from pathlib import Path

from chameleon.mfe_v2_screen import build_v2_sufficiency_screen


class MFEV2SufficiencyScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.rows = build_v2_sufficiency_screen(cls.root)

    def test_closed_form_scale_and_screen_counts(self) -> None:
        self.assertEqual(len(self.rows), 54)
        self.assertTrue(all(row.capacity_pass for row in self.rows))
        self.assertEqual(
            sum(row.battery_alone_energy_pass for row in self.rows), 21
        )
        self.assertAlmostEqual(
            self.rows[0].load_scale,
            0.12973491536034124,
            places=15,
        )

    def test_committed_csv_matches_closed_form_rows(self) -> None:
        path = (
            self.root
            / "tests"
            / "fixtures"
            / "mfe_v2_sufficiency_screen.csv"
        )
        with path.open(newline="", encoding="utf-8") as handle:
            committed = list(csv.DictReader(handle))
        self.assertEqual(len(committed), len(self.rows))
        for expected, actual in zip(self.rows, committed):
            self.assertEqual(actual["cell_id"], expected.cell_id)
            self.assertAlmostEqual(
                float(actual["load_scale"]), expected.load_scale, places=15
            )
            self.assertAlmostEqual(
                float(actual["capacity_required_mw"]),
                expected.capacity_required_mw,
                places=9,
            )
            self.assertAlmostEqual(
                float(actual["sequential_energy_lb_mwh"]),
                expected.sequential_energy_lb_mwh,
                places=9,
            )
            self.assertEqual(
                actual["battery_alone_energy_pass"],
                str(expected.battery_alone_energy_pass).lower(),
            )
            self.assertEqual(actual["energy_label"], expected.energy_label)


if __name__ == "__main__":
    unittest.main()

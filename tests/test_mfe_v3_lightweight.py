from __future__ import annotations

import unittest

from chameleon.mfe_v3_lightweight import (
    CONSTRUCTION_SCENARIOS,
    HELD_OUT_SCENARIOS,
    cell_grid,
)


class MFEV3LightweightTests(unittest.TestCase):
    def test_registered_lightweight_grid(self) -> None:
        cells = cell_grid()
        self.assertEqual(len(cells), 6)
        self.assertEqual(
            {(cell.duration_hours, cell.reserve_fraction) for cell in cells},
            {
                (1, 0.05),
                (1, 0.20),
                (2, 0.05),
                (2, 0.20),
                (4, 0.05),
                (4, 0.20),
            },
        )
        self.assertTrue(all(cell.initial_soc_fraction == 0.50 for cell in cells))
        self.assertTrue(all(cell.sigma == 0.08 for cell in cells))

    def test_registered_scenario_counts_are_lightweight(self) -> None:
        self.assertEqual(CONSTRUCTION_SCENARIOS, 32)
        self.assertEqual(HELD_OUT_SCENARIOS, 32)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from chameleon.contracts import ContractKind
from chameleon.mfe_frontier import (
    MFECell,
    generate_pv_shortfall_scenarios,
    replay_frontier_schedule,
    solve_frontier_schedule,
    static_parameter_grid,
)
from chameleon.mfe_harness import load_frozen_deterministic_case


class ReducedMFEFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case = load_frozen_deterministic_case(Path(__file__).resolve().parents[1])
        cls.cell = MFECell(4, 1.0, 0.08, 0.05)
        cls.scenarios = generate_pv_shortfall_scenarios(
            cls.case.must_take_pv_mw, 0.08, 8, 2026072901
        )

    def test_scenario_generator_is_reproducible_and_one_sided(self) -> None:
        repeated = generate_pv_shortfall_scenarios(
            self.case.must_take_pv_mw, 0.08, 8, 2026072901
        )
        np.testing.assert_allclose(self.scenarios, repeated)
        self.assertTrue(
            np.all(self.scenarios <= np.asarray(self.case.must_take_pv_mw) + 1e-12)
        )
        self.assertTrue(np.all(self.scenarios >= 0.0))

    def test_prefix_and_lifted_full_agree_and_replay(self) -> None:
        prefix = solve_frontier_schedule(
            self.case, self.cell, self.scenarios, ContractKind.C1_PREFIX
        )
        full = solve_frontier_schedule(
            self.case, self.cell, self.scenarios, ContractKind.C_FULL_DET
        )
        self.assertAlmostEqual(prefix.objective, full.objective, places=6)
        # The two exact formulations may select different members of a
        # degenerate optimal face; equality of objective and physical replay
        # is the invariant, not equality of the serialized optimizer witness.
        for schedule in (prefix, full):
            replay = replay_frontier_schedule(schedule, self.cell, self.scenarios)
            self.assertAlmostEqual(replay.non_delivery_rate, 0.0)

    def test_static_parameter_grid_is_frozen(self) -> None:
        grid = static_parameter_grid()
        self.assertEqual(len(grid), 660)
        self.assertTrue(
            all(item.power_cap_mw + item.reserve_cap_mw <= 50 for item in grid)
        )


if __name__ == "__main__":
    unittest.main()

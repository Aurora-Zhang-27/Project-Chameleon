from __future__ import annotations

import unittest
from pathlib import Path

from chameleon.contracts import ContractKind
from chameleon.mfe_harness import (
    load_frozen_deterministic_case,
    solve_deterministic_mfe_case,
)


class DeterministicMFEHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.case = load_frozen_deterministic_case(cls.root)
        cls.results = {
            contract: solve_deterministic_mfe_case(cls.case, contract)
            for contract in (
                ContractKind.C0_EXACT_MARGINAL,
                ContractKind.C1_PREFIX,
                ContractKind.C_FULL_DET,
            )
        }

    def test_frozen_case_and_data_dimensions(self) -> None:
        self.assertEqual(self.case.study_date.isoformat(), "2020-03-30")
        self.assertEqual(self.case.battery.horizon, 24)
        self.assertEqual(len(self.case.thermal_units), 4)
        self.assertEqual(
            tuple(unit.uid for unit in self.case.thermal_units),
            ("123_STEAM_3", "115_STEAM_3", "101_STEAM_3", "113_CT_1"),
        )
        self.assertAlmostEqual(max(self.case.must_take_pv_mw), 200.0)

    def test_hourly_balance_reserve_and_headroom(self) -> None:
        for contract, result in self.results.items():
            with self.subTest(contract=contract):
                for t in range(24):
                    supply = (
                        result.battery_injection_mw[t]
                        + self.case.must_take_pv_mw[t]
                        + sum(row[t] for row in result.thermal_dispatch_mw)
                    )
                    reserve = result.battery_upward_reserve_mw[t] + sum(
                        row[t] for row in result.thermal_upward_reserve_mw
                    )
                    self.assertAlmostEqual(supply, self.case.load_mw[t], places=7)
                    self.assertGreaterEqual(
                        reserve + 1e-7,
                        self.case.upward_reserve_requirement_mw[t],
                    )
                    self.assertLessEqual(
                        result.battery_injection_mw[t]
                        + result.battery_upward_reserve_mw[t],
                        self.case.battery.power_max_mw + 1e-7,
                    )
                    for unit, dispatch, unit_reserve in zip(
                        self.case.thermal_units,
                        result.thermal_dispatch_mw,
                        result.thermal_upward_reserve_mw,
                    ):
                        self.assertGreaterEqual(dispatch[t] + 1e-7, unit.power_min_mw)
                        self.assertLessEqual(
                            dispatch[t] + unit_reserve[t],
                            unit.power_max_mw + 1e-7,
                        )

    def test_c0_soc_failure_and_prefix_full_repair(self) -> None:
        c0 = self.results[ContractKind.C0_EXACT_MARGINAL]
        c1 = self.results[ContractKind.C1_PREFIX]
        full = self.results[ContractKind.C_FULL_DET]

        self.assertGreater(sum(c0.replay.base_energy_violation_mwh), 1e-6)
        self.assertAlmostEqual(c1.replay.total_reserve_shortfall_mwh, 0.0)
        self.assertAlmostEqual(full.replay.total_reserve_shortfall_mwh, 0.0)
        self.assertAlmostEqual(sum(c1.replay.base_energy_violation_mwh), 0.0)
        self.assertAlmostEqual(sum(full.replay.base_energy_violation_mwh), 0.0)
        self.assertAlmostEqual(c1.objective, full.objective, places=6)
        self.assertLessEqual(c0.objective, c1.objective + 1e-7)

    def test_full_lifted_soc_matches_independent_replay(self) -> None:
        result = self.results[ContractKind.C_FULL_DET]
        self.assertIsNotNone(result.lifted_soc_mwh)
        assert result.lifted_soc_mwh is not None
        replay_path = (
            result.replay.soc_start_mwh[0],
            *result.replay.soc_base_end_mwh,
        )
        self.assertEqual(len(replay_path), len(result.lifted_soc_mwh))
        for replayed, lifted in zip(replay_path, result.lifted_soc_mwh):
            self.assertAlmostEqual(replayed, lifted, places=7)


if __name__ == "__main__":
    unittest.main()

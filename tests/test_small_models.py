from __future__ import annotations

import unittest
from fractions import Fraction

from chameleon.contracts import (
    BatteryGeometry,
    ContractKind,
    c0_exact_marginal_feasible,
    enumerate_grid_trajectories,
    exact_local_grid_pairs,
    exact_local_grid_projection,
    full_projected_feasible,
    prefix_feasible,
    strict_c0_witness,
)
from chameleon.model import BatterySpec, DispatchCase, solve_dispatch
from chameleon.replay import replay_base_and_single_calls


class TwoPeriodCounterexampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.battery = BatterySpec(
            horizon=2,
            initial_energy_mwh=1.0,
            power_max_mw=1.0,
        )
        self.case = DispatchCase(
            battery=self.battery,
            load_mw=(1.0, 0.0),
            reserve_requirement_mw=(0.0, 1.0),
        )

    def test_exact_marginal_contract_fails_in_replay(self) -> None:
        result = solve_dispatch(self.case, ContractKind.C0_EXACT_MARGINAL)
        replay = replay_base_and_single_calls(
            self.battery,
            result.hybrid_energy_mw,
            result.hybrid_reserve_mw,
        )

        self.assertAlmostEqual(result.objective, 0.0)
        self.assertTupleAlmostEqual(result.hybrid_energy_mw, (1.0, 0.0))
        self.assertAlmostEqual(result.hybrid_reserve_mw[1], 1.0)
        self.assertTupleAlmostEqual(replay.soc_start_mwh, (1.0, 0.0))
        self.assertTupleAlmostEqual(replay.soc_base_end_mwh, (0.0, 0.0))
        self.assertAlmostEqual(replay.reserve_shortfall_mw[1], 1.0)
        self.assertAlmostEqual(replay.total_reserve_shortfall_mwh, 1.0)

    def test_single_prefix_cut_eliminates_failure(self) -> None:
        prefix = solve_dispatch(self.case, ContractKind.C1_PREFIX)
        full = solve_dispatch(self.case, ContractKind.C_FULL_DET)

        for result in (prefix, full):
            replay = replay_base_and_single_calls(
                self.battery,
                result.hybrid_energy_mw,
                result.hybrid_reserve_mw,
            )
            self.assertAlmostEqual(result.objective, 10.0)
            self.assertTupleAlmostEqual(result.hybrid_energy_mw, (1.0, 0.0))
            self.assertAlmostEqual(result.hybrid_reserve_mw[1], 0.0)
            self.assertAlmostEqual(result.thermal_reserve_mw[1], 1.0)
            self.assertAlmostEqual(replay.total_reserve_shortfall_mwh, 0.0)

        lifted_soc = full.lifted_soc_mwh
        self.assertIsNotNone(lifted_soc)
        assert lifted_soc is not None
        self.assertTupleAlmostEqual(lifted_soc, (1.0, 0.0, 0.0))

    def test_market_contract_is_only_a_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            solve_dispatch(self.case, ContractKind.C0_MARKET)

    def test_reserve_shortfall_energy_respects_sustain_duration(self) -> None:
        battery = BatterySpec(
            horizon=2,
            initial_energy_mwh=1.0,
            power_max_mw=1.0,
            reserve_duration_hours=0.5,
        )
        case = DispatchCase(
            battery=battery,
            load_mw=(1.0, 0.0),
            reserve_requirement_mw=(0.0, 1.0),
        )

        c0 = solve_dispatch(case, ContractKind.C0_EXACT_MARGINAL)
        replay = replay_base_and_single_calls(
            battery, c0.hybrid_energy_mw, c0.hybrid_reserve_mw
        )
        prefix = solve_dispatch(case, ContractKind.C1_PREFIX)

        self.assertAlmostEqual(c0.objective, 0.0)
        self.assertAlmostEqual(replay.reserve_shortfall_mw[1], 1.0)
        self.assertAlmostEqual(replay.reserve_shortfall_mwh[1], 0.5)
        self.assertAlmostEqual(replay.total_reserve_shortfall_mwh, 0.5)
        self.assertAlmostEqual(prefix.objective, 10.0)

    def assertTupleAlmostEqual(
        self,
        actual: tuple[float, ...],
        expected: tuple[float, ...],
        places: int = 8,
    ) -> None:
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value, places=places)


class ExactSetTests(unittest.TestCase):
    def test_prefix_equals_lifted_full_on_three_to_six_period_grids(self) -> None:
        for horizon in range(3, 7):
            with self.subTest(horizon=horizon):
                geometry = BatteryGeometry(
                    horizon=horizon,
                    initial_energy=Fraction(1),
                    power_max=Fraction(1),
                )
                prefix = set(
                    enumerate_grid_trajectories(
                        geometry, ContractKind.C1_PREFIX, Fraction(1, 2)
                    )
                )
                full = set(
                    enumerate_grid_trajectories(
                        geometry, ContractKind.C_FULL_DET, Fraction(1, 2)
                    )
                )
                self.assertEqual(prefix, full)

    def test_analytic_local_marginal_matches_full_projection(self) -> None:
        for horizon in range(3, 7):
            geometry = BatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                power_max=Fraction(1),
            )
            expected = exact_local_grid_pairs(geometry, Fraction(1, 2))
            for period in range(horizon):
                with self.subTest(horizon=horizon, period=period):
                    projected = exact_local_grid_projection(
                        geometry, period, Fraction(1, 2)
                    )
                    self.assertEqual(projected, expected)

    def test_full_is_strict_subset_of_c0_when_energy_couples_periods(self) -> None:
        geometry = BatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1),
            power_max=Fraction(1),
        )
        witness = strict_c0_witness(geometry)
        self.assertIsNotNone(witness)
        assert witness is not None
        self.assertTrue(c0_exact_marginal_feasible(geometry, *witness))
        self.assertFalse(prefix_feasible(geometry, *witness))
        self.assertFalse(full_projected_feasible(geometry, *witness))

    def test_gap_disappears_when_energy_is_nonbinding(self) -> None:
        for horizon in range(3, 7):
            geometry = BatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(horizon),
                power_max=Fraction(1),
            )
            c0 = set(
                enumerate_grid_trajectories(
                    geometry, ContractKind.C0_EXACT_MARGINAL, Fraction(1)
                )
            )
            prefix = set(
                enumerate_grid_trajectories(
                    geometry, ContractKind.C1_PREFIX, Fraction(1)
                )
            )
            full = set(
                enumerate_grid_trajectories(
                    geometry, ContractKind.C_FULL_DET, Fraction(1)
                )
            )
            self.assertEqual(c0, prefix)
            self.assertEqual(prefix, full)

            battery = BatterySpec(
                horizon=horizon,
                initial_energy_mwh=float(horizon),
                power_max_mw=1.0,
            )
            case = DispatchCase(
                battery=battery,
                load_mw=(0.5,) * horizon,
                reserve_requirement_mw=(0.5,) * horizon,
            )
            results = [
                solve_dispatch(case, kind)
                for kind in (
                    ContractKind.C0_EXACT_MARGINAL,
                    ContractKind.C1_PREFIX,
                    ContractKind.C_FULL_DET,
                )
            ]
            for result in results:
                replay = replay_base_and_single_calls(
                    battery,
                    result.hybrid_energy_mw,
                    result.hybrid_reserve_mw,
                )
                self.assertAlmostEqual(result.objective, 0.0)
                self.assertAlmostEqual(
                    replay.total_reserve_shortfall_mwh, 0.0
                )

    def test_three_to_six_period_dispatch_failure_and_repair(self) -> None:
        for horizon in range(3, 7):
            load = (1.0,) + (0.0,) * (horizon - 1)
            reserve = (0.0,) * (horizon - 1) + (1.0,)
            battery = BatterySpec(
                horizon=horizon,
                initial_energy_mwh=1.0,
                power_max_mw=1.0,
            )
            case = DispatchCase(
                battery=battery,
                load_mw=load,
                reserve_requirement_mw=reserve,
            )

            c0 = solve_dispatch(case, ContractKind.C0_EXACT_MARGINAL)
            prefix = solve_dispatch(case, ContractKind.C1_PREFIX)
            full = solve_dispatch(case, ContractKind.C_FULL_DET)

            c0_replay = replay_base_and_single_calls(
                battery, c0.hybrid_energy_mw, c0.hybrid_reserve_mw
            )
            prefix_replay = replay_base_and_single_calls(
                battery, prefix.hybrid_energy_mw, prefix.hybrid_reserve_mw
            )
            full_replay = replay_base_and_single_calls(
                battery, full.hybrid_energy_mw, full.hybrid_reserve_mw
            )

            with self.subTest(horizon=horizon):
                self.assertAlmostEqual(c0.objective, 0.0)
                self.assertAlmostEqual(c0_replay.reserve_shortfall_mw[-1], 1.0)
                self.assertAlmostEqual(prefix.objective, 10.0)
                self.assertAlmostEqual(full.objective, 10.0)
                self.assertAlmostEqual(
                    prefix_replay.total_reserve_shortfall_mwh, 0.0
                )
                self.assertAlmostEqual(
                    full_replay.total_reserve_shortfall_mwh, 0.0
                )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import product

from chameleon.charging import BidirectionalBatteryGeometry
from chameleon.pv import (
    DeterministicPVGeometry,
    HybridAction,
    HybridReserveWitness,
    find_reserve_witness,
    replay_reserve_witness,
)
from chameleon.sequential import (
    Activation,
    ReserveSourcePolicy,
    activation_conditioned_reachability,
    find_sequential_witness,
    replay_sequential_witness,
)


def _counterexample_geometry(horizon: int) -> DeterministicPVGeometry:
    battery = BidirectionalBatteryGeometry(
        horizon=horizon,
        initial_energy=Fraction(1),
        energy_min=Fraction(0),
        energy_max=Fraction(1),
        charge_power_max=Fraction(1),
        discharge_power_max=Fraction(1),
    )
    return DeterministicPVGeometry(
        battery,
        (Fraction(1),) + (Fraction(0),) * (horizon - 1),
    )


class SequentialCounterexampleTests(unittest.TestCase):
    def test_same_one_shot_tuple_has_different_second_call_capability(
        self,
    ) -> None:
        geometry = _counterexample_geometry(3)
        idle = HybridAction(0, 0, 0)
        base = (idle, idle, idle)
        down = base
        solar_first = HybridReserveWitness(
            base,
            (
                HybridAction(1, 0, 0),
                HybridAction(0, 0, 1),
                idle,
            ),
            down,
        )
        battery_first = HybridReserveWitness(
            base,
            (
                HybridAction(0, 0, 1),
                HybridAction(0, 0, 1),
                idle,
            ),
            down,
        )
        h = (Fraction(0),) * 3
        r_up = (Fraction(1), Fraction(1), Fraction(0))
        r_down = (Fraction(0),) * 3
        calls = (Activation.UP, Activation.UP, Activation.NONE)

        # Both source choices pass the old isolated replay because each call
        # is evaluated from the common nominal base SOC trajectory.
        isolated_solar = replay_reserve_witness(
            geometry, h, r_up, r_down, solar_first
        )
        isolated_battery = replay_reserve_witness(
            geometry, h, r_up, r_down, battery_first
        )
        self.assertTrue(isolated_solar.physical_feasible)
        self.assertTrue(isolated_battery.physical_feasible)

        sequential_solar = replay_sequential_witness(
            geometry, h, r_up, r_down, calls, solar_first
        )
        sequential_battery = replay_sequential_witness(
            geometry, h, r_up, r_down, calls, battery_first
        )
        self.assertTrue(sequential_solar.physical_feasible)
        self.assertEqual(
            sequential_solar.realized_soc_path,
            (Fraction(1), Fraction(1), Fraction(0), Fraction(0)),
        )
        self.assertFalse(sequential_battery.physical_feasible)
        self.assertEqual(
            sequential_battery.realized_soc_path[:3],
            (Fraction(1), Fraction(0), Fraction(-1)),
        )

    def test_source_labels_remove_the_counterexample_ambiguity(self) -> None:
        geometry = _counterexample_geometry(3)
        h = (Fraction(0),) * 3
        r_up = (Fraction(1), Fraction(1), Fraction(0))
        zero = (Fraction(0),) * 3
        calls = (Activation.UP, Activation.UP, Activation.NONE)

        unrestricted = find_sequential_witness(
            geometry, h, r_up, zero, calls
        )
        labelled = find_sequential_witness(
            geometry,
            h,
            r_up,
            zero,
            calls,
            upward_source=(
                ReserveSourcePolicy.PV_ONLY,
                ReserveSourcePolicy.BATTERY_ONLY,
                ReserveSourcePolicy.ANY,
            ),
        )
        battery_only = find_sequential_witness(
            geometry,
            h,
            r_up,
            zero,
            calls,
            upward_source=ReserveSourcePolicy.BATTERY_ONLY,
        )

        self.assertIsNotNone(unrestricted)
        self.assertIsNotNone(labelled)
        self.assertIsNone(battery_only)
        assert labelled is not None
        replay = replay_sequential_witness(
            geometry,
            h,
            r_up,
            zero,
            calls,
            labelled,
            upward_source=(
                ReserveSourcePolicy.PV_ONLY,
                ReserveSourcePolicy.BATTERY_ONLY,
                ReserveSourcePolicy.ANY,
            ),
        )
        self.assertTrue(replay.physical_feasible)


class SequentialEnumerationTests(unittest.TestCase):
    def test_isolated_product_is_strictly_optimistic_for_repeated_up_calls(
        self,
    ) -> None:
        for horizon in range(3, 7):
            geometry = _counterexample_geometry(horizon)
            h = (Fraction(0),) * horizon
            zero = (Fraction(0),) * horizon
            calls = (Activation.UP,) * horizon
            isolated_count = 0
            sequential_count = 0

            for r_up in product(
                (Fraction(0), Fraction(1)), repeat=horizon
            ):
                isolated = find_reserve_witness(
                    geometry, h, r_up, zero, Fraction(1)
                )
                sequential = find_sequential_witness(
                    geometry, h, r_up, zero, calls, Fraction(1)
                )
                interval = activation_conditioned_reachability(
                    geometry, h, r_up, zero, calls
                )
                if isolated is not None:
                    isolated_count += 1
                if sequential is not None:
                    sequential_count += 1
                    replay = replay_sequential_witness(
                        geometry, h, r_up, zero, calls, sequential
                    )
                    self.assertTrue(replay.physical_feasible)
                self.assertEqual(sequential is not None, interval.feasible)

            with self.subTest(horizon=horizon):
                self.assertEqual(isolated_count, 2**horizon)
                self.assertEqual(sequential_count, 2 * horizon)
                self.assertLess(sequential_count, isolated_count)

    def test_lossy_mode_aware_interval_matches_grid_for_three_to_six(
        self,
    ) -> None:
        for horizon in range(3, 7):
            battery = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(1),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
                charge_efficiency=Fraction(1, 2),
                discharge_efficiency=Fraction(1, 2),
            )
            geometry = DeterministicPVGeometry(
                battery,
                (Fraction(1, 2),)
                + (Fraction(0),) * (horizon - 1),
            )
            h = (Fraction(0),) * horizon
            zero = (Fraction(0),) * horizon
            calls = (Activation.UP,) * horizon
            sequential_count = 0

            for r_up in product(
                (Fraction(0), Fraction(1, 2)), repeat=horizon
            ):
                witness = find_sequential_witness(
                    geometry,
                    h,
                    r_up,
                    zero,
                    calls,
                    Fraction(1, 2),
                )
                interval = activation_conditioned_reachability(
                    geometry, h, r_up, zero, calls
                )
                self.assertEqual(witness is not None, interval.feasible)
                if witness is not None:
                    sequential_count += 1
                    replay = replay_sequential_witness(
                        geometry, h, r_up, zero, calls, witness
                    )
                    self.assertTrue(replay.physical_feasible)

            with self.subTest(horizon=horizon):
                self.assertEqual(sequential_count, 2 * horizon)

    def test_lossy_transition_graph_retains_nonconvexity(self) -> None:
        battery = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1, 2),
            energy_min=Fraction(0),
            energy_max=Fraction(1),
            charge_power_max=Fraction(1),
            discharge_power_max=Fraction(1),
            charge_efficiency=Fraction(4, 5),
            discharge_efficiency=Fraction(4, 5),
        )
        geometry = DeterministicPVGeometry(
            battery, (Fraction(1, 5),) * 3
        )
        a = (Fraction(-3, 5), Fraction(0), Fraction(0))
        b = (Fraction(1, 5), Fraction(-9, 10), Fraction(0))
        midpoint = tuple((x + y) / 2 for x, y in zip(a, b))
        zero = (Fraction(0),) * 3
        calls = (Activation.NONE,) * 3

        self.assertTrue(
            activation_conditioned_reachability(
                geometry, a, zero, zero, calls
            ).feasible
        )
        self.assertTrue(
            activation_conditioned_reachability(
                geometry, b, zero, zero, calls
            ).feasible
        )
        self.assertFalse(
            activation_conditioned_reachability(
                geometry, midpoint, zero, zero, calls
            ).feasible
        )


if __name__ == "__main__":
    unittest.main()

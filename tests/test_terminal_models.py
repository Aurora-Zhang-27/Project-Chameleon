from __future__ import annotations

import unittest
from fractions import Fraction

from chameleon.charging import (
    BidirectionalBatteryGeometry,
    ChargingContractKind,
    enumerate_signed_grid_trajectories,
    full_physical_feasible,
    mode_aware_prefix_feasible,
    two_sided_linear_prefix_feasible,
)
from chameleon.terminal import (
    enumerate_relaxed_terminal_net_grid,
    full_with_terminal_feasible,
    lossless_terminal_cut_feasible,
    mode_aware_terminal_cut_feasible,
    prefix_with_terminal_feasible,
    relaxed_with_terminal_feasible,
    replay_terminal_soc,
)


class DischargeOnlyTerminalTests(unittest.TestCase):
    def test_previous_contract_needs_terminal_cut(self) -> None:
        geometry = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1),
            energy_min=Fraction(0),
            energy_max=Fraction(1),
            charge_power_max=Fraction(0),
            discharge_power_max=Fraction(1),
        )
        p = (Fraction(1), Fraction(0), Fraction(0))
        target = Fraction(1, 2)

        self.assertTrue(two_sided_linear_prefix_feasible(geometry, p))
        self.assertTrue(full_physical_feasible(geometry, p))
        self.assertFalse(lossless_terminal_cut_feasible(geometry, p, target))
        replay = replay_terminal_soc(geometry, p, target)
        self.assertEqual(replay.soc_path, (Fraction(1), 0, 0, 0))
        self.assertEqual(replay.terminal_shortfall, Fraction(1, 2))
        self.assertFalse(replay.physically_feasible)

    def test_prefix_plus_terminal_cut_is_exact_for_three_to_six_periods(
        self,
    ) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(1),
                charge_power_max=Fraction(0),
                discharge_power_max=Fraction(1),
            )
            target = Fraction(1, 2)
            candidates = tuple(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.UPPER_ONLY_LINEAR_PREFIX,
                    Fraction(1, 2),
                    include_reserve=True,
                )
            )
            prefix_terminal = {
                (p, r)
                for p, r in candidates
                if prefix_with_terminal_feasible(
                    geometry,
                    ChargingContractKind.TWO_SIDED_LINEAR_PREFIX,
                    p,
                    target,
                    r,
                )
            }
            full_terminal = {
                (p, r)
                for p, r in candidates
                if full_with_terminal_feasible(
                    geometry, p, target, r
                )
            }
            with self.subTest(horizon=horizon):
                self.assertEqual(prefix_terminal, full_terminal)


class BidirectionalLosslessTerminalTests(unittest.TestCase):
    def test_two_sided_prefix_plus_terminal_cut_is_exact(self) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            target = Fraction(1)
            candidates = tuple(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.UPPER_ONLY_LINEAR_PREFIX,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            prefix_terminal = {
                (p, r)
                for p, r in candidates
                if prefix_with_terminal_feasible(
                    geometry,
                    ChargingContractKind.TWO_SIDED_LINEAR_PREFIX,
                    p,
                    target,
                    r,
                )
            }
            full_terminal = {
                (p, r)
                for p, r in candidates
                if full_with_terminal_feasible(
                    geometry, p, target, r
                )
            }
            with self.subTest(horizon=horizon):
                self.assertEqual(prefix_terminal, full_terminal)

    def test_lossless_relaxation_remains_exact_with_terminal_cut(self) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            target = Fraction(1)
            full_net = frozenset(
                p
                for p, r in enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY,
                    Fraction(1),
                    include_reserve=False,
                )
                if full_with_terminal_feasible(
                    geometry, p, target, r
                )
            )
            relaxed_net = enumerate_relaxed_terminal_net_grid(
                geometry, target, Fraction(1)
            )
            with self.subTest(horizon=horizon):
                self.assertEqual(full_net, relaxed_net)


class BidirectionalLossyTerminalTests(unittest.TestCase):
    def test_mode_aware_prefix_plus_terminal_cut_is_exact(self) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(3),
                energy_min=Fraction(0),
                energy_max=Fraction(5),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
                charge_efficiency=Fraction(4, 5),
                discharge_efficiency=Fraction(4, 5),
            )
            target = Fraction(2)
            candidates = tuple(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.UPPER_ONLY_LINEAR_PREFIX,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            prefix_terminal = {
                (p, r)
                for p, r in candidates
                if prefix_with_terminal_feasible(
                    geometry,
                    ChargingContractKind.MODE_AWARE_PREFIX,
                    p,
                    target,
                    r,
                )
            }
            full_terminal = {
                (p, r)
                for p, r in candidates
                if full_with_terminal_feasible(
                    geometry, p, target, r
                )
            }
            with self.subTest(horizon=horizon):
                self.assertEqual(prefix_terminal, full_terminal)

    def test_nonconvexity_and_strict_relaxation_survive_terminal_target(
        self,
    ) -> None:
        geometry = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1, 2),
            energy_min=Fraction(0),
            energy_max=Fraction(1),
            charge_power_max=Fraction(1),
            discharge_power_max=Fraction(1),
            charge_efficiency=Fraction(4, 5),
            discharge_efficiency=Fraction(4, 5),
        )
        target = Fraction(19, 20)
        a = (Fraction(-3, 5), Fraction(0), Fraction(0))
        b = (Fraction(1, 5), Fraction(-9, 10), Fraction(0))
        midpoint = tuple((a_t + b_t) / 2 for a_t, b_t in zip(a, b))

        replay_a = replay_terminal_soc(geometry, a, target)
        replay_b = replay_terminal_soc(geometry, b, target)
        replay_mid = replay_terminal_soc(geometry, midpoint, target)

        self.assertTrue(replay_a.physically_feasible)
        self.assertTrue(replay_b.physically_feasible)
        self.assertEqual(replay_a.terminal_energy, Fraction(49, 50))
        self.assertEqual(replay_b.terminal_energy, Fraction(97, 100))
        self.assertFalse(replay_mid.physically_feasible)
        self.assertFalse(replay_mid.base_bounds_satisfied)
        self.assertTrue(
            mode_aware_terminal_cut_feasible(geometry, a, target)
        )
        self.assertTrue(
            mode_aware_terminal_cut_feasible(geometry, b, target)
        )

        relaxed_charge = (
            Fraction(3, 10),
            Fraction(9, 20),
            Fraction(0),
        )
        relaxed_discharge = (
            Fraction(1, 10),
            Fraction(0),
            Fraction(0),
        )
        self.assertTrue(
            relaxed_with_terminal_feasible(
                geometry,
                relaxed_charge,
                relaxed_discharge,
                target,
            )
        )
        self.assertFalse(
            full_with_terminal_feasible(
                geometry, midpoint, target
            )
        )


if __name__ == "__main__":
    unittest.main()

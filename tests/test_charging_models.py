from __future__ import annotations

import unittest
from fractions import Fraction

from chameleon.charging import (
    BidirectionalBatteryGeometry,
    ChargingContractKind,
    enumerate_relaxed_net_grid_trajectories,
    enumerate_signed_grid_trajectories,
    full_physical_feasible,
    mode_aware_prefix_feasible,
    relaxed_split_feasible,
    two_sided_linear_prefix_feasible,
    upper_only_linear_prefix_feasible,
)


class LosslessChargingTests(unittest.TestCase):
    def test_upper_only_prefix_misses_overcharge(self) -> None:
        geometry = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1),
            energy_min=Fraction(0),
            energy_max=Fraction(1),
            charge_power_max=Fraction(1),
            discharge_power_max=Fraction(1),
        )
        net_power = (Fraction(-1, 2), Fraction(0), Fraction(0))

        self.assertTrue(
            upper_only_linear_prefix_feasible(geometry, net_power)
        )
        self.assertFalse(full_physical_feasible(geometry, net_power))
        self.assertFalse(
            two_sided_linear_prefix_feasible(geometry, net_power)
        )

    def test_two_sided_linear_prefix_is_exact_for_lossless_model(self) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            two_sided = set(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.TWO_SIDED_LINEAR_PREFIX,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            full = set(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            with self.subTest(horizon=horizon):
                self.assertEqual(two_sided, full)

    def test_lossless_convex_relaxation_has_same_net_projection(self) -> None:
        for horizon in range(3, 7):
            geometry = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            full_net = frozenset(
                p
                for p, _ in enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY,
                    Fraction(1),
                    include_reserve=False,
                )
            )
            relaxed_net = enumerate_relaxed_net_grid_trajectories(
                geometry, Fraction(1)
            )
            with self.subTest(horizon=horizon):
                self.assertEqual(full_net, relaxed_net)


class LossyChargingTests(unittest.TestCase):
    def test_naive_linear_prefix_is_neither_inner_nor_outer(self) -> None:
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

        # Naive linear upper bound admits 0.5 MWh discharge, but the physical
        # battery needs 0.625 MWh because eta_d = 0.8.
        false_positive = (
            Fraction(1, 2),
            Fraction(0),
            Fraction(0),
        )
        self.assertTrue(
            two_sided_linear_prefix_feasible(geometry, false_positive)
        )
        self.assertFalse(full_physical_feasible(geometry, false_positive))

        # Naive lower bound rejects 0.6 MWh charging, but only 0.48 MWh reaches
        # SOC because eta_c = 0.8, so the physical trajectory remains feasible.
        false_negative = (
            Fraction(-3, 5),
            Fraction(0),
            Fraction(0),
        )
        self.assertFalse(
            two_sided_linear_prefix_feasible(geometry, false_negative)
        )
        self.assertTrue(full_physical_feasible(geometry, false_negative))

    def test_mode_aware_prefix_matches_full_for_three_to_six_periods(self) -> None:
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
            mode_aware = set(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.MODE_AWARE_PREFIX,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            full = set(
                enumerate_signed_grid_trajectories(
                    geometry,
                    ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY,
                    Fraction(1),
                    include_reserve=True,
                )
            )
            with self.subTest(horizon=horizon):
                self.assertEqual(mode_aware, full)

    def test_exact_net_projection_is_nonconvex_and_relaxation_is_strict(self) -> None:
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

        trajectory_a = (
            Fraction(-3, 5),
            Fraction(0),
            Fraction(0),
        )
        trajectory_b = (
            Fraction(1, 5),
            Fraction(-9, 10),
            Fraction(0),
        )
        midpoint = tuple(
            (a_t + b_t) / 2
            for a_t, b_t in zip(trajectory_a, trajectory_b)
        )

        self.assertTrue(full_physical_feasible(geometry, trajectory_a))
        self.assertTrue(full_physical_feasible(geometry, trajectory_b))
        self.assertFalse(full_physical_feasible(geometry, midpoint))
        self.assertFalse(mode_aware_prefix_feasible(geometry, midpoint))

        # The midpoint of the two lifted physical witnesses uses simultaneous
        # charge/discharge in period 1 and is feasible only in the convex
        # relaxation:
        # c = (0.3, 0.45, 0), d = (0.1, 0, 0).
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
        self.assertEqual(
            midpoint,
            tuple(
                d_t - c_t
                for c_t, d_t in zip(relaxed_charge, relaxed_discharge)
            ),
        )
        self.assertTrue(
            relaxed_split_feasible(
                geometry, relaxed_charge, relaxed_discharge
            )
        )


if __name__ == "__main__":
    unittest.main()

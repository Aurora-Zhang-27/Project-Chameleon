from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import product

from chameleon.charging import (
    BidirectionalBatteryGeometry,
    ChargingContractKind,
    enumerate_signed_grid_trajectories,
)
from chameleon.pv import (
    DeterministicPVGeometry,
    HybridAction,
    HybridReserveWitness,
    enumerate_hybrid_projection,
    enumerate_reserve_projection,
    exact_hybrid_reachability,
    must_take_contract_feasible,
    replay_hybrid_schedule,
    replay_reserve_witness,
    translated_battery_power,
)


class MustTakePVTests(unittest.TestCase):
    def test_affine_translation_is_exact_for_three_to_six_periods(self) -> None:
        for horizon in range(3, 7):
            battery = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            pv = DeterministicPVGeometry(
                battery, (Fraction(1),) * horizon
            )
            explicit = set(
                enumerate_hybrid_projection(
                    pv, Fraction(1), must_take=True
                )
            )
            translated = {
                tuple(p_t + Fraction(1) for p_t in p)
                for p, _ in enumerate_signed_grid_trajectories(
                    battery,
                    ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY,
                    Fraction(1),
                    include_reserve=False,
                )
            }
            with self.subTest(horizon=horizon):
                self.assertEqual(explicit, translated)
                for h in explicit:
                    self.assertEqual(
                        translated_battery_power(pv, h),
                        tuple(h_t - 1 for h_t in h),
                    )
                    self.assertTrue(
                        must_take_contract_feasible(
                            pv,
                            h,
                            ChargingContractKind.TWO_SIDED_LINEAR_PREFIX,
                        )
                    )


class CurtailedPVTests(unittest.TestCase):
    def test_lossless_reachable_interval_matches_grid_projection(self) -> None:
        for horizon in range(3, 7):
            battery = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1),
                energy_min=Fraction(0),
                energy_max=Fraction(2),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            pv = DeterministicPVGeometry(
                battery, (Fraction(1),) * horizon
            )
            explicit = set(enumerate_hybrid_projection(pv, Fraction(1)))
            candidates = set(
                product(
                    (
                        Fraction(-1),
                        Fraction(0),
                        Fraction(1),
                        Fraction(2),
                    ),
                    repeat=horizon,
                )
            )
            interval_projection = {
                h
                for h in candidates
                if exact_hybrid_reachability(pv, h).feasible
            }
            with self.subTest(horizon=horizon):
                self.assertEqual(explicit, interval_projection)

    def test_same_hybrid_schedule_has_different_soc_implications(self) -> None:
        battery = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(0),
            energy_min=Fraction(0),
            energy_max=Fraction(2),
            charge_power_max=Fraction(1),
            discharge_power_max=Fraction(1),
            charge_efficiency=Fraction(4, 5),
            discharge_efficiency=Fraction(4, 5),
        )
        pv = DeterministicPVGeometry(
            battery, (Fraction(1), Fraction(0), Fraction(0))
        )
        idle = HybridAction(0, 0, 0)
        curtail_all = (idle, idle, idle)
        charge_from_pv = (
            HybridAction(1, 1, 0),
            idle,
            idle,
        )

        replay_a = replay_hybrid_schedule(pv, curtail_all)
        replay_b = replay_hybrid_schedule(pv, charge_from_pv)
        self.assertTrue(replay_a.physical_feasible)
        self.assertTrue(replay_b.physical_feasible)
        self.assertEqual(replay_a.hybrid_injection, (0, 0, 0))
        self.assertEqual(replay_b.hybrid_injection, (0, 0, 0))
        self.assertEqual(replay_a.soc_path[-1], Fraction(0))
        self.assertEqual(replay_b.soc_path[-1], Fraction(4, 5))

    def test_lossy_projection_need_not_be_convex(self) -> None:
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
        pv = DeterministicPVGeometry(
            battery, (Fraction(1, 5),) * 3
        )
        a = (Fraction(-3, 5), Fraction(0), Fraction(0))
        b = (Fraction(1, 5), Fraction(-9, 10), Fraction(0))
        midpoint = tuple((x + y) / 2 for x, y in zip(a, b))

        self.assertTrue(exact_hybrid_reachability(pv, a).feasible)
        self.assertTrue(exact_hybrid_reachability(pv, b).feasible)
        self.assertFalse(exact_hybrid_reachability(pv, midpoint).feasible)

        idle = HybridAction(0, 0, 0)
        replay_a = replay_hybrid_schedule(
            pv,
            (
                HybridAction(0, Fraction(3, 5), 0),
                idle,
                idle,
            ),
        )
        replay_b = replay_hybrid_schedule(
            pv,
            (
                HybridAction(0, 0, Fraction(1, 5)),
                HybridAction(0, Fraction(9, 10), 0),
                idle,
            ),
        )
        self.assertTrue(replay_a.physical_feasible)
        self.assertTrue(replay_b.physical_feasible)
        self.assertEqual(replay_a.hybrid_injection, a)
        self.assertEqual(replay_b.hybrid_injection, b)

        relaxed_midpoint = replay_hybrid_schedule(
            pv,
            (
                HybridAction(0, Fraction(3, 10), Fraction(1, 10)),
                HybridAction(0, Fraction(9, 20), 0),
                idle,
            ),
        )
        self.assertEqual(relaxed_midpoint.hybrid_injection, midpoint)
        self.assertFalse(relaxed_midpoint.physical_feasible)
        self.assertTrue(relaxed_midpoint.relaxed_feasible)

    def test_lossy_grid_projection_is_exactly_replayed_for_three_to_six(
        self,
    ) -> None:
        for horizon in range(3, 7):
            battery = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(2),
                energy_min=Fraction(0),
                energy_max=Fraction(4),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
                charge_efficiency=Fraction(1, 2),
                discharge_efficiency=Fraction(1, 2),
            )
            pv = DeterministicPVGeometry(
                battery, (Fraction(1),) * horizon
            )
            witnesses = enumerate_hybrid_projection(pv, Fraction(1))
            candidates = set(
                product(
                    (
                        Fraction(-1),
                        Fraction(0),
                        Fraction(1),
                        Fraction(2),
                    ),
                    repeat=horizon,
                )
            )
            interval_projection = {
                h
                for h in candidates
                if exact_hybrid_reachability(pv, h).feasible
            }
            self.assertEqual(set(witnesses), interval_projection)
            for h, actions in witnesses.items():
                replay = replay_hybrid_schedule(pv, actions)
                self.assertTrue(replay.physical_feasible)
                self.assertEqual(replay.hybrid_injection, h)
                self.assertTrue(exact_hybrid_reachability(pv, h).feasible)


class PVReserveTests(unittest.TestCase):
    def test_same_external_upward_reserve_has_two_energy_sources(self) -> None:
        battery = BidirectionalBatteryGeometry(
            horizon=3,
            initial_energy=Fraction(1),
            energy_min=Fraction(0),
            energy_max=Fraction(2),
            charge_power_max=Fraction(1),
            discharge_power_max=Fraction(1),
        )
        pv = DeterministicPVGeometry(
            battery, (Fraction(1), Fraction(0), Fraction(0))
        )
        idle = HybridAction(0, 0, 0)
        base = (idle, idle, idle)
        downward = base
        solar_witness = HybridReserveWitness(
            base,
            (HybridAction(1, 0, 0), idle, idle),
            downward,
        )
        battery_witness = HybridReserveWitness(
            base,
            (HybridAction(0, 0, 1), idle, idle),
            downward,
        )
        h = (Fraction(0),) * 3
        r_up = (Fraction(1), Fraction(0), Fraction(0))
        r_down = (Fraction(0),) * 3

        solar = replay_reserve_witness(
            pv, h, r_up, r_down, solar_witness
        )
        stored = replay_reserve_witness(
            pv, h, r_up, r_down, battery_witness
        )
        self.assertTrue(solar.physical_feasible)
        self.assertTrue(stored.physical_feasible)
        self.assertEqual(solar.upward_source[0], (1, 0, 0))
        self.assertEqual(stored.upward_source[0], (0, 0, 1))
        self.assertEqual(solar.upward_branch_end_energy[0], Fraction(1))
        self.assertEqual(stored.upward_branch_end_energy[0], Fraction(0))

        # The downward analogue: the same (h=1, r-=1) can be delivered by
        # curtailing PV or by charging the battery.
        pv_base = (HybridAction(1, 0, 0), idle, idle)
        curtailed = HybridReserveWitness(
            pv_base,
            pv_base,
            (HybridAction(0, 0, 0), idle, idle),
        )
        charging = HybridReserveWitness(
            pv_base,
            pv_base,
            (HybridAction(1, 1, 0), idle, idle),
        )
        h_down = (Fraction(1), Fraction(0), Fraction(0))
        r_down_call = (Fraction(1), Fraction(0), Fraction(0))
        curtailed_replay = replay_reserve_witness(
            pv, h_down, r_down, r_down_call, curtailed
        )
        charging_replay = replay_reserve_witness(
            pv, h_down, r_down, r_down_call, charging
        )
        self.assertTrue(curtailed_replay.physical_feasible)
        self.assertTrue(charging_replay.physical_feasible)
        self.assertEqual(
            curtailed_replay.downward_source[0], (1, 0, 0)
        )
        self.assertEqual(
            charging_replay.downward_source[0], (0, 1, 0)
        )
        self.assertEqual(
            curtailed_replay.downward_branch_end_energy[0], Fraction(1)
        )
        self.assertEqual(
            charging_replay.downward_branch_end_energy[0], Fraction(2)
        )

    def test_up_and_down_grid_witnesses_replay_for_three_to_six(self) -> None:
        for horizon in range(3, 7):
            battery = BidirectionalBatteryGeometry(
                horizon=horizon,
                initial_energy=Fraction(1, 2),
                energy_min=Fraction(0),
                energy_max=Fraction(1),
                charge_power_max=Fraction(1),
                discharge_power_max=Fraction(1),
            )
            pv = DeterministicPVGeometry(
                battery, (Fraction(1),) * horizon
            )
            for direction in ("up", "down"):
                projected = enumerate_reserve_projection(
                    pv,
                    (Fraction(0), Fraction(1)),
                    (Fraction(0), Fraction(1)),
                    Fraction(1),
                    direction=direction,
                )
                self.assertTrue(projected)
                self.assertLess(len(projected), 4**horizon)
                zero = (Fraction(0),) * horizon
                for (h, reserve), witness in projected.items():
                    up = reserve if direction == "up" else zero
                    down = reserve if direction == "down" else zero
                    replay = replay_reserve_witness(
                        pv, h, up, down, witness
                    )
                    self.assertTrue(replay.physical_feasible)

    def test_reserve_relaxation_is_outer_and_can_be_strict(self) -> None:
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
        pv = DeterministicPVGeometry(
            battery, (Fraction(1, 2),) * 3
        )
        h_values = (
            Fraction(-1, 2),
            Fraction(0),
            Fraction(1, 2),
            Fraction(1),
        )
        reserve_values = (Fraction(0), Fraction(1, 2))
        physical = enumerate_reserve_projection(
            pv,
            h_values,
            reserve_values,
            Fraction(1, 2),
            direction="down",
        )
        relaxed = enumerate_reserve_projection(
            pv,
            h_values,
            reserve_values,
            Fraction(1, 2),
            direction="down",
            relaxed=True,
        )
        self.assertLess(set(physical), set(relaxed))

        strict_key = next(iter(set(relaxed) - set(physical)))
        h, r_down = strict_key
        zero = (Fraction(0),) * 3
        replay = replay_reserve_witness(
            pv, h, zero, r_down, relaxed[strict_key]
        )
        self.assertTrue(replay.relaxed_feasible)
        self.assertFalse(replay.physical_feasible)


if __name__ == "__main__":
    unittest.main()

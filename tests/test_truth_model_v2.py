from __future__ import annotations

import unittest
from dataclasses import replace

from chameleon.mfe_harness import ThermalUnit
from chameleon.mfe_v2_contracts import C0Parameters, PVBand
from chameleon.replay_v2 import replay_v2
from chameleon.truth_model import (
    Stage1Decision,
    V2BatterySpec,
    V2System,
    solve_extensive_form,
    solve_stage2,
    solve_wait_and_see,
)


def _system(
    *,
    load: float = 100.0,
    forecast_pv: float = 50.0,
    initial_energy: float = 25.0,
    reserve_fraction: float = 0.05,
) -> V2System:
    unit = ThermalUnit(
        uid="TEST",
        power_min_mw=0.0,
        power_max_mw=200.0,
        ramp_mw_per_hour=200.0,
        segment_widths_mw=(200.0,),
        segment_costs_per_mwh=(20.0,),
    )
    return V2System(
        load_mw=(load,) * 24,
        forecast_pv_mw=(forecast_pv,) * 24,
        thermal_units=(unit,),
        battery=V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=initial_energy,
        ),
        reserve_fraction=reserve_fraction,
    )


def _stage1(
    system: V2System,
    *,
    hybrid: float = 50.0,
    hybrid_up: float | None = None,
    hybrid_down: float | None = None,
) -> Stage1Decision:
    requirement = system.reserve_fraction * system.load_mw[0]
    rup = requirement if hybrid_up is None else hybrid_up
    rdn = requirement if hybrid_down is None else hybrid_down
    thermal = system.load_mw[0] - hybrid
    return Stage1Decision(
        thermal_dispatch_mw=((thermal,) * 24,),
        hybrid_injection_mw=(hybrid,) * 24,
        thermal_up_reserve_mw=((0.0,) * 24,),
        thermal_down_reserve_mw=((0.0,) * 24,),
        hybrid_up_reserve_mw=(rup,) * 24,
        hybrid_down_reserve_mw=(rdn,) * 24,
    )


class TruthModelV2Tests(unittest.TestCase):
    def test_idle_case_replays_and_reconciles_cost(self) -> None:
        system = _system()
        stage1 = _stage1(system)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        self.assertIsNotNone(solved.decision)
        self.assertFalse(solved.diagnostics.solver_unresolved)
        assert solved.decision is not None
        replay = replay_v2(system, stage1, solved.decision, system.forecast_pv_mw)
        self.assertTrue(replay.physically_valid, replay.physical_violations)
        self.assertTrue(replay.cost_reconciled)

    def test_soc_efficiency_has_correct_charge_and_discharge_direction(self) -> None:
        system = _system()
        stage1 = _stage1(system)
        pv = list(system.forecast_pv_mw)
        pv[0] = 60.0
        pv[1] = 40.0
        solved = solve_stage2(system, stage1, pv)
        assert solved.decision is not None
        decision = solved.decision
        self.assertGreater(decision.charge_mw[0], 9.9)
        self.assertGreater(decision.discharge_mw[1], 9.9)
        expected_1 = 25.0 + 0.95 * decision.charge_mw[0]
        expected_2 = expected_1 - decision.discharge_mw[1] / 0.95
        self.assertAlmostEqual(decision.soc_mwh[1], expected_1, places=6)
        self.assertAlmostEqual(decision.soc_mwh[2], expected_2, places=6)

    def test_binary_mode_prevents_simultaneous_charge_discharge(self) -> None:
        system = _system()
        stage1 = _stage1(system)
        pv = tuple(60.0 if t % 2 == 0 else 40.0 for t in range(24))
        solved = solve_stage2(system, stage1, pv)
        assert solved.decision is not None
        for c, d, z in zip(
            solved.decision.charge_mw,
            solved.decision.discharge_mw,
            solved.decision.mode_discharge,
        ):
            self.assertFalse(c > 1e-6 and d > 1e-6)
            self.assertEqual(z, 1 if d > 1e-6 else 0 if c > 1e-6 else z)

    def test_terminal_soc_is_enforced(self) -> None:
        system = _system(initial_energy=12.5)
        stage1 = _stage1(system)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        self.assertGreaterEqual(solved.decision.soc_mwh[-1], 12.5 - 1e-6)

    def test_isolated_up_and_down_calls_are_replayed(self) -> None:
        system = _system()
        stage1 = _stage1(system, hybrid_up=5.0, hybrid_down=5.0)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        replay = replay_v2(system, stage1, solved.decision, system.forecast_pv_mw)
        self.assertAlmostEqual(replay.activation.shortfall_up_mw[0], 0.0)
        self.assertAlmostEqual(replay.activation.shortfall_down_mw[0], 0.0)
        self.assertGreaterEqual(replay.activation.up_mid_soc_mwh[0], -1e-6)
        self.assertLessEqual(
            replay.activation.down_mid_soc_mwh[0],
            system.battery.energy_capacity_mwh + 1e-6,
        )

    def test_sequential_calls_carry_actual_soc_without_reset(self) -> None:
        system = _system(initial_energy=40.0)
        stage1 = _stage1(system, hybrid_up=5.0, hybrid_down=5.0)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        replay = replay_v2(system, stage1, solved.decision, system.forecast_pv_mw)
        base_hour_18 = solved.decision.soc_mwh[17]
        self.assertAlmostEqual(replay.sequential.actual_soc_mwh[17], base_hour_18)
        self.assertLess(
            replay.sequential.actual_soc_mwh[19],
            solved.decision.soc_mwh[19],
        )
        self.assertEqual(len(replay.sequential.call_mid_soc_mwh), 2)

    def test_replay_rejects_tampered_primal_trajectory(self) -> None:
        system = _system()
        stage1 = _stage1(system)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        tampered_charge = list(solved.decision.charge_mw)
        tampered_charge[0] = 3.0
        tampered = replace(solved.decision, charge_mw=tuple(tampered_charge))
        replay = replay_v2(system, stage1, tampered, system.forecast_pv_mw)
        self.assertFalse(replay.physically_valid)
        self.assertFalse(replay.cost_reconciled)

    def test_penalty_cost_is_independently_recomputed(self) -> None:
        system = _system(load=300.0, forecast_pv=0.0)
        stage1 = _stage1(system, hybrid=100.0, hybrid_up=15.0, hybrid_down=15.0)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        replay = replay_v2(system, stage1, solved.decision, system.forecast_pv_mw)
        components = dict(replay.cost_components)
        self.assertGreater(components["load_shedding"], 0.0)
        self.assertGreater(components["imbalance"], 0.0)
        self.assertTrue(replay.cost_reconciled)

    def test_solver_diagnostics_record_registered_fields(self) -> None:
        system = _system()
        stage1 = _stage1(system)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        diagnostics = solved.diagnostics
        self.assertGreater(diagnostics.variable_count, 0)
        self.assertGreater(diagnostics.constraint_count, 0)
        self.assertEqual(diagnostics.binary_count, 72)
        self.assertIsNotNone(diagnostics.best_bound)
        self.assertIsNotNone(diagnostics.relative_gap)

    def test_extensive_full_has_common_stage1_and_replayable_scenarios(self) -> None:
        system = _system()
        paths = (
            system.forecast_pv_mw,
            tuple(value + 2.0 for value in system.forecast_pv_mw),
        )
        result = solve_extensive_form(system, paths, "c_full")
        self.assertIsNotNone(result.stage1)
        self.assertEqual(len(result.scenarios), 2)
        assert result.stage1 is not None
        for path, decision in zip(paths, result.scenarios):
            replay = replay_v2(system, result.stage1, decision, path)
            self.assertTrue(replay.physically_valid, replay.physical_violations)
            self.assertTrue(replay.cost_reconciled)

    def test_c0_and_c1_change_only_stage1_contract_constraints(self) -> None:
        system = _system()
        path = (system.forecast_pv_mw,)
        c0 = solve_extensive_form(
            system,
            path,
            "c0",
            c0_parameters=C0Parameters(10.0, 5.0, 5.0, 50.0),
        )
        band = PVBand(
            sigma=0.08,
            lower_quantile=0.01,
            upper_quantile=0.99,
            lower_mw=system.forecast_pv_mw,
            upper_mw=system.forecast_pv_mw,
            path_count=2_000,
            seed=2026080105,
            path_digest_sha256="0" * 64,
        )
        c1 = solve_extensive_form(system, path, "c1", c1_band=band)
        self.assertIsNotNone(c0.stage1)
        self.assertIsNotNone(c1.stage1)
        self.assertEqual(c0.diagnostics.binary_count, c1.diagnostics.binary_count)
        self.assertEqual(c0.diagnostics.binary_count, 72)

    def test_wait_and_see_is_one_path_revealed_solve(self) -> None:
        system = _system()
        result = solve_wait_and_see(system, system.forecast_pv_mw)
        self.assertIsNotNone(result.stage1)
        self.assertEqual(len(result.scenarios), 1)
        self.assertFalse(result.diagnostics.solver_unresolved)

    def test_day_ahead_spill_makes_stage1_economically_complete(self) -> None:
        unit = ThermalUnit(
            uid="MUST_RUN",
            power_min_mw=100.0,
            power_max_mw=200.0,
            ramp_mw_per_hour=200.0,
            segment_widths_mw=(100.0,),
            segment_costs_per_mwh=(20.0,),
        )
        system = V2System(
            load_mw=(0.0,) * 24,
            forecast_pv_mw=(0.0,) * 24,
            thermal_units=(unit,),
            battery=V2BatterySpec(
                energy_capacity_mwh=50.0,
                initial_energy_mwh=25.0,
            ),
            reserve_fraction=0.0,
        )
        result = solve_extensive_form(system, (system.forecast_pv_mw,), "c_full")
        self.assertIsNotNone(result.stage1)
        assert result.stage1 is not None
        self.assertGreater(sum(result.stage1.day_ahead_spill_mw), 0.0)
        replay = replay_v2(
            system,
            result.stage1,
            result.scenarios[0],
            system.forecast_pv_mw,
        )
        self.assertTrue(replay.cost_reconciled)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import replace

import pytest

from chameleon.mfe_harness import ThermalUnit
from chameleon.relaxation_v4 import (
    diagnose_simultaneous_operation,
    recover_modes_if_complementary,
    solve_adaptive_extensive_form,
)
from chameleon.replay_v2 import replay_v2
from chameleon.truth_model import (
    SolverConfig,
    Stage1Decision,
    V2BatterySpec,
    V2System,
    solve_stage2,
    solve_extensive_form,
    validate_assoc_declaration,
)


def _system() -> V2System:
    unit = ThermalUnit(
        uid="V4-TEST",
        power_min_mw=0.0,
        power_max_mw=200.0,
        ramp_mw_per_hour=200.0,
        segment_widths_mw=(200.0,),
        segment_costs_per_mwh=(20.0,),
    )
    return V2System(
        load_mw=(100.0,) * 24,
        forecast_pv_mw=(50.0,) * 24,
        thermal_units=(unit,),
        battery=V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=25.0,
        ),
        reserve_fraction=0.05,
    )


def _stage1(system: V2System) -> Stage1Decision:
    return Stage1Decision(
        thermal_dispatch_mw=((50.0,) * system.horizon,),
        hybrid_injection_mw=(50.0,) * system.horizon,
        thermal_up_reserve_mw=((0.0,) * system.horizon,),
        thermal_down_reserve_mw=((0.0,) * system.horizon,),
        hybrid_up_reserve_mw=(5.0,) * system.horizon,
        hybrid_down_reserve_mw=(5.0,) * system.horizon,
    )


def test_relaxed_stage2_has_no_integer_variables() -> None:
    system = _system()
    solved = solve_stage2(
        system,
        _stage1(system),
        system.forecast_pv_mw,
        config=SolverConfig(
            relax_base_modes=True,
            relax_up_activation_modes=True,
            relax_down_activation_modes=True,
        ),
    )
    assert solved.decision is not None
    assert solved.diagnostics.binary_count == 0
    assert not solved.diagnostics.solver_unresolved


def test_mode_only_recovery_replays_when_actions_are_complementary() -> None:
    system = _system()
    stage1 = _stage1(system)
    solved = solve_stage2(
        system,
        stage1,
        system.forecast_pv_mw,
        config=SolverConfig(
            relax_base_modes=True,
            relax_up_activation_modes=True,
            relax_down_activation_modes=True,
        ),
    )
    assert solved.decision is not None
    report = diagnose_simultaneous_operation(solved.decision)
    assert report.max_simultaneous_mw <= 1e-6
    recovered = recover_modes_if_complementary(solved.decision)
    assert recovered is not None
    replay = replay_v2(system, stage1, recovered, system.forecast_pv_mw)
    assert replay.physically_valid, replay.physical_violations
    assert replay.cost_reconciled


def test_adaptive_integrality_certifies_a_high_reserve_case() -> None:
    system = _system()
    system = V2System(
        **{
            **system.__dict__,
            "reserve_fraction": 0.20,
        }
    )
    paths = (
        system.forecast_pv_mw,
        tuple(value * 1.08 for value in system.forecast_pv_mw),
    )
    adaptive = solve_adaptive_extensive_form(
        system,
        paths,
        "c_full",
        config=SolverConfig(mip_rel_gap=1e-8),
    )
    assert adaptive.certified_contract_exact
    assert adaptive.result.stage1 is not None
    assert adaptive.iterations
    assert adaptive.result.diagnostics.binary_count < 3 * system.horizon * len(paths)
    for pv, decision in zip(paths, adaptive.result.scenarios):
        replay = replay_v2(system, adaptive.result.stage1, decision, pv)
        assert replay.physically_valid, replay.physical_violations
        assert replay.cost_reconciled


def test_c_assoc_declares_and_replays_a_physical_soc_path() -> None:
    system = _system()
    solved = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_assoc",
    )
    assert solved.stage1 is not None
    validate_assoc_declaration(system, solved.stage1)
    assert len(solved.stage1.declared_soc_mwh) == system.horizon + 1
    replay = replay_v2(
        system,
        solved.stage1,
        solved.scenarios[0],
        system.forecast_pv_mw,
    )
    assert replay.physically_valid, replay.physical_violations
    assert replay.cost_reconciled


def test_c_assoc_rejects_power_feasible_but_energy_infeasible_award() -> None:
    system = _system()
    solved = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_assoc",
    )
    assert solved.stage1 is not None
    excessive_up = list(solved.stage1.hybrid_up_reserve_mw)
    excessive_up[0] = 48.0
    invalid = replace(
        solved.stage1,
        hybrid_injection_mw=(50.0,) * system.horizon,
        hybrid_up_reserve_mw=tuple(excessive_up),
        declared_soc_mwh=(25.0,) * (system.horizon + 1),
        declared_charge_mw=(0.0,) * system.horizon,
        declared_discharge_mw=(0.0,) * system.horizon,
        declared_pv_curtailment_mw=(0.0,) * system.horizon,
    )
    with pytest.raises(ValueError, match="upward energy"):
        validate_assoc_declaration(system, invalid)

from __future__ import annotations

import unittest

from chameleon.mfe_harness import ThermalUnit
from chameleon.mfe_v2_contracts import (
    PVBand,
    evaluate_c1_v3_envelope,
)
from chameleon.mfe_v3_certificates import (
    certify_v2_c1_nonempty,
    certify_v3_reference_and_reserve,
)
from chameleon.replay_v2 import replay_v2
from chameleon.truth_model import (
    Stage1Decision,
    V2BatterySpec,
    V2System,
    solve_extensive_form,
    solve_stage2,
)


def _band(lower: float = 50.0, upper: float = 60.0) -> PVBand:
    return PVBand(
        sigma=0.08,
        lower_quantile=0.01,
        upper_quantile=0.99,
        lower_mw=(lower,) * 24,
        upper_mw=(upper,) * 24,
        path_count=2_000,
        seed=2026080105,
        path_digest_sha256="0" * 64,
    )


def _system(initial_energy: float = 25.0) -> V2System:
    return V2System(
        load_mw=(100.0,) * 24,
        forecast_pv_mw=(50.0,) * 24,
        thermal_units=(
            ThermalUnit(
                uid="TEST",
                power_min_mw=0.0,
                power_max_mw=200.0,
                ramp_mw_per_hour=200.0,
                segment_widths_mw=(200.0,),
                segment_costs_per_mwh=(20.0,),
            ),
        ),
        battery=V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=initial_energy,
        ),
        reserve_fraction=0.05,
    )


def _stage1(system: V2System, reserve: float = 5.0) -> Stage1Decision:
    return Stage1Decision(
        thermal_dispatch_mw=((50.0,) * 24,),
        hybrid_injection_mw=(50.0,) * 24,
        thermal_up_reserve_mw=((0.0,) * 24,),
        thermal_down_reserve_mw=((0.0,) * 24,),
        hybrid_up_reserve_mw=(reserve,) * 24,
        hybrid_down_reserve_mw=(reserve,) * 24,
    )


class MFEV3Tests(unittest.TestCase):
    def test_v2_certificate_detects_band_width_failure(self) -> None:
        battery = V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=25.0,
        )
        certificate = certify_v2_c1_nonempty(battery, _band())
        self.assertFalse(certificate.nonempty)
        self.assertLess(certificate.margin_mwh, 0.0)

    def test_v3_reference_is_nonempty_and_capacity_is_positive(self) -> None:
        battery = V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=25.0,
        )
        certificate = certify_v3_reference_and_reserve(battery, _band())
        self.assertTrue(certificate.reference_nonempty)
        self.assertEqual(certificate.reference_schedule_mw, (50.0,) * 24)
        self.assertGreater(certificate.max_two_sided_reserve_mw, 0.0)

    def test_v3_envelope_accepts_reference_and_rejects_terminal_exhaustion(self) -> None:
        battery = V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=25.0,
        )
        accepted = evaluate_c1_v3_envelope(
            battery,
            (50.0,) * 24,
            (5.0,) * 24,
            (5.0,) * 24,
            _band(),
        )
        self.assertTrue(accepted.accepted, accepted.violations)
        rejected = evaluate_c1_v3_envelope(
            battery,
            (51.0,) * 24,
            (0.0,) * 24,
            (0.0,) * 24,
            _band(),
        )
        self.assertFalse(rejected.accepted)
        self.assertIn("terminal discharge budget", rejected.violations)

    def test_v3_envelope_rejects_downward_power_and_energy(self) -> None:
        battery = V2BatterySpec(
            energy_capacity_mwh=50.0,
            initial_energy_mwh=49.0,
        )
        evaluation = evaluate_c1_v3_envelope(
            battery,
            (0.0,) * 24,
            (0.0,) * 24,
            (51.0,) * 24,
            _band(lower=0.0, upper=10.0),
        )
        self.assertFalse(evaluation.accepted)
        self.assertTrue(
            {"downward power at hour 1", "downward energy at hour 1"}
            <= set(evaluation.violations)
        )

    def test_activated_branches_have_independent_complementary_modes(self) -> None:
        system = _system()
        stage1 = _stage1(system, reserve=5.0)
        solved = solve_stage2(system, stage1, system.forecast_pv_mw)
        assert solved.decision is not None
        decision = solved.decision
        replay = replay_v2(system, stage1, decision, system.forecast_pv_mw)
        self.assertTrue(replay.physically_valid, replay.physical_violations)
        for t in range(system.horizon):
            up_c = decision.charge_mw[t] - decision.up_charge_reduction_mw[t]
            up_d = (
                decision.discharge_mw[t]
                + decision.up_discharge_increase_mw[t]
            )
            down_c = (
                decision.charge_mw[t]
                + decision.down_charge_increase_mw[t]
            )
            down_d = (
                decision.discharge_mw[t]
                - decision.down_discharge_reduction_mw[t]
            )
            self.assertFalse(up_c > 1e-6 and up_d > 1e-6)
            self.assertFalse(down_c > 1e-6 and down_d > 1e-6)

    def test_c1_v3_extensive_form_uses_exact_positive_part(self) -> None:
        system = _system()
        result = solve_extensive_form(
            system,
            (system.forecast_pv_mw,),
            "c1_v3",
            c1_band=_band(lower=50.0, upper=60.0),
        )
        self.assertIsNotNone(result.stage1)
        self.assertEqual(result.diagnostics.binary_count, 96)
        assert result.stage1 is not None
        evaluation = evaluate_c1_v3_envelope(
            system.battery,
            result.stage1.hybrid_injection_mw,
            result.stage1.hybrid_up_reserve_mw,
            result.stage1.hybrid_down_reserve_mw,
            _band(lower=50.0, upper=60.0),
        )
        self.assertTrue(evaluation.accepted, evaluation.violations)


if __name__ == "__main__":
    unittest.main()

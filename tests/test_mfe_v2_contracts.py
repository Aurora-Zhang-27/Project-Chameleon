from __future__ import annotations

import unittest

import numpy as np

from chameleon.mfe_v2_contracts import (
    BAND_SEED,
    PVBand,
    build_registered_c1_bands,
    c0_finalists,
    evaluate_c1_envelope,
    generate_pv_paths_by_level,
)
from chameleon.truth_model import V2BatterySpec


class MFEV2ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.forecast = tuple([0.0] * 6 + [100.0] * 12 + [0.0] * 6)
        self.battery = V2BatterySpec(
            energy_capacity_mwh=200.0,
            initial_energy_mwh=100.0,
        )

    def test_band_generator_is_reproducible_two_sided_and_clipped(self) -> None:
        first = generate_pv_paths_by_level(
            self.forecast, count_per_level=20, seed=BAND_SEED
        )
        second = generate_pv_paths_by_level(
            self.forecast, count_per_level=20, seed=BAND_SEED
        )
        for sigma in (0.03, 0.08, 0.15):
            np.testing.assert_array_equal(first[sigma], second[sigma])
            self.assertTrue(np.all(first[sigma] >= 0.0))
            self.assertTrue(np.all(first[sigma] <= 200.0))
            positive = first[sigma][:, 8]
            self.assertTrue(np.any(positive < 100.0))
            self.assertTrue(np.any(positive > 100.0))

    def test_registered_bands_have_frozen_quantiles_and_count(self) -> None:
        bands = build_registered_c1_bands(
            self.forecast, count_per_level=50, seed=BAND_SEED
        )
        self.assertEqual(set(bands), {"1/99", "5/95"})
        primary = bands["1/99"][0.08]
        diagnostic = bands["5/95"][0.08]
        self.assertEqual(primary.path_count, 50)
        self.assertEqual(primary.seed, BAND_SEED)
        self.assertLessEqual(primary.lower_mw[8], diagnostic.lower_mw[8])
        self.assertGreaterEqual(primary.upper_mw[8], diagnostic.upper_mw[8])
        self.assertEqual(len(primary.path_digest_sha256), 64)

    def test_c1_accepts_zero_residual_schedule(self) -> None:
        band = PVBand(
            sigma=0.08,
            lower_quantile=0.01,
            upper_quantile=0.99,
            lower_mw=(0.0,) * 24,
            upper_mw=(0.0,) * 24,
            path_count=2_000,
            seed=BAND_SEED,
            path_digest_sha256="0" * 64,
        )
        evaluation = evaluate_c1_envelope(
            self.battery,
            (0.0,) * 24,
            (0.0,) * 24,
            (0.0,) * 24,
            band,
        )
        self.assertTrue(evaluation.accepted)

    def test_c1_rejects_discharge_prefix_and_terminal_cut(self) -> None:
        band = PVBand(
            sigma=0.08,
            lower_quantile=0.01,
            upper_quantile=0.99,
            lower_mw=(0.0,) * 24,
            upper_mw=(0.0,) * 24,
            path_count=2_000,
            seed=BAND_SEED,
            path_digest_sha256="0" * 64,
        )
        evaluation = evaluate_c1_envelope(
            self.battery,
            (10.0,) * 24,
            (0.0,) * 24,
            (0.0,) * 24,
            band,
        )
        self.assertFalse(evaluation.accepted)
        self.assertIn("terminal cut", evaluation.violations)
        self.assertTrue(any("upper prefix" in item for item in evaluation.violations))

    def test_c0_pruning_returns_at_most_twelve_registered_points(self) -> None:
        finalists = c0_finalists(self.battery)
        self.assertGreater(len(finalists), 0)
        self.assertLessEqual(len(finalists), 12)
        for item in finalists:
            self.assertEqual(item.power_cap_mw % 5.0, 0.0)
            self.assertLessEqual(
                item.power_cap_mw + item.up_reserve_cap_mw, 50.0
            )
            self.assertLessEqual(
                item.power_cap_mw + item.down_reserve_cap_mw, 50.0
            )

    def test_primary_band_has_closed_form_empty_set_certificate(self) -> None:
        bands = build_registered_c1_bands(self.forecast)
        band = bands["1/99"][0.08]
        total_width = sum(
            upper - lower
            for lower, upper in zip(band.lower_mw, band.upper_mw)
        )
        necessary_two_sided_energy = 0.95 * total_width
        self.assertGreater(
            necessary_two_sided_energy,
            self.battery.energy_capacity_mwh,
        )


if __name__ == "__main__":
    unittest.main()

# MFE final scenario-staircase gate decision

Date: 2026-07-30

Decision: **freeze `N=32`; retain `C_full-32` and fitted `C0`.**

The result was reached under
`MFE_FINAL_SCENARIO_STAIRCASE_AMENDMENT_2026-07-30.md`, before generating
held-out seed `2026080104`.

## `C_full-32`

| Sentinel | Certified | Gap | Total adaptive solve | Final binaries | Independent replay |
|---|---:|---:|---:|---:|---:|
| S1: 1h, 75% SOC, sigma .15, 20% reserve | yes | 0 | 72.04 s | 736 | 32/32 pass |
| S2: 2h, 50% SOC, sigma .08, 20% reserve | yes | effectively 0 | 7.96 s | 736 | 32/32 pass |
| S3: 4h, 25% SOC, sigma .03, 5% reserve | yes | effectively 0 | 6.57 s | 672 | 32/32 pass |

All three returned the sandwich certificate within 900 seconds and the
registered 0.1% gap. No base-trajectory mode required integrality; all
restored binaries were in isolated reserve-activation branches.

## `C0` fit

All 12 preregistered finalists resolved and certified in each sentinel.
Each fit selected:

`(power cap, up reserve cap, down reserve cap, ramp cap) =
(15, 35, 35, 50)`.

This parameter tuple is not reused merely because it appeared in the earlier
fixture. It re-emerged from the frozen N=32 candidate comparison.

## Consequence

The staircase stops at its first passing level. `N=16` is not run. The
held-out line is named `C_full-32`, and every paper table must disclose that
its 32-scenario stage-1 estimate can be weaker or more variable than the
unavailable 384-scenario optimum, biasing relative contract comparisons in
the contracts' favor.


# MFE v3 lightweight full-binary pilot

Date: 2026-08-01

Status: exploratory local feasibility check. This does not replace the frozen
lean paper validation or support powered market claims.

## Design

The pilot reduces repeated solves without changing the 24-hour truth model:

- six cells: storage duration in `{1h, 2h, 4h}` and reserve in `{5%, 20%}`;
- initial SOC fixed at 50%;
- PV error fixed at `sigma = 0.08`;
- 32 construction scenarios with seed `2026080101`;
- 32 common held-out paths with seed `2026080104`;
- four lines: `C0-fixture`, `C1`, `C_ASSOC`, and full-binary `C_full-32`;
- complete charge/discharge mode binaries retained;
- 24-hour horizon, losses, curtailment, recourse, reserve activation, and
  terminal SOC retained;
- one numerical thread.

## Computational result

All six `C_full-32` solves reached the registered 0.1% relative-gap target.
Solve time ranged from 2.19 seconds to 60.10 seconds; the sum of the six
reported solver times was 113.94 seconds. The two 1-hour cells were the only
ones requiring more than five seconds.

Each cell produced 128 held-out records, for 768 total records. Across the
six cells there were:

- zero construction physical replay failures;
- zero construction cost-reconciliation failures;
- zero held-out physical replay failures;
- zero held-out cost-reconciliation failures;
- zero unresolved held-out stage-2 solves.

## Descriptive cost direction

Across the six 32-path cells, mean realized `C1` cost was 10.66%-13.94% below
`C_ASSOC`. Mean `C1` cost remained 1.05%-2.48% above `C_full-32`.

These are small-sample descriptive comparisons. They show that the original
v3 full-binary design is locally executable after reducing scenario and grid
replication; they do not provide powered statistical inference or CAISO-wide
performance estimates.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
PYTHONPATH=src python -m chameleon.mfe_v3_lightweight all \
  --output results/mfe_v3_lightweight_full_binary
```

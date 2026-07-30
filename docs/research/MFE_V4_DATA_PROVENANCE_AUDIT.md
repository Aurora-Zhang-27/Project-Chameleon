# MFE v4 data-provenance audit

Date: 2026-07-30

Status: passed for a pinned public benchmark; not evidence that the inputs are
observed CAISO operations.

## 1. What is locally present

The MFE input snapshot comes from the public NREL/DOE Grid Modernization
Laboratory Consortium RTS-GMLC repository at upstream commit
`3ece0d3725c844056132393ee252b3083dd4eab4`. The local files were checked both
by SHA-256 (recorded in `data/external/rts_gmlc/README.md`) and by exact Git
blob identity against that upstream commit.

| Local file | Role in Chameleon | Upstream Git blob | Verification |
|---|---|---:|---|
| `gen.csv` | four-unit thermal source table | `f7811443081656378ff00a15578129d73e83f048` | exact match |
| `reserves.csv` | retained source context | `99c899eddf06e69385aa238737c2e3352863b662` | exact match |
| `DAY_AHEAD_pv.csv` | aggregate PV shape | `ee97be0fd5f28c4a550db46d70b46f9d9e52a934` | exact match |
| `DAY_AHEAD_regional_Load.csv` | three-region load | `6f0ef99beb7fd06fd9aecbfd8eb73d2e9393742e` | exact match |
| `DAY_AHEAD_regional_Flex_Up.csv` | retained source context | `f91d522c8cd951d7ad5b28e6081a7b41e2ba2296` | exact match |
| `DAY_AHEAD_regional_Flex_Down.csv` | retained source context | `b7a1487bcf9b465e5e9c3b8d01b67ab1fabdc7ad` | exact match |

The locally retained CAISO tariff and business-practice documents are primary
sources for the proposed `C_ASSOC` rule crosswalk. They are not numerical
operating data.

## 2. Truth classification

RTS-GMLC is a genuine, public, version-pinned research benchmark. Its numbers
are synthetic test-system data, however, rather than measurements of a real
CAISO fleet or a real operating day. Accordingly:

- reproducibility and source-integrity gate: **pass**;
- benchmark-data authenticity gate: **pass**;
- observed-market-data / external-validity gate: **not yet satisfied**.

No paper, figure, table, or repository text may describe the RTS-GMLC inputs
as “real CAISO data.” Permitted descriptions are “public RTS-GMLC benchmark,”
“pinned synthetic test-system data,” or equivalent.

## 3. v4 data policy

The computational-equivalence and runtime gates use the pinned RTS-GMLC
snapshot so they remain comparable with v1-v3. Synthetic toy cases may be
used only for unit tests and smallest counterexamples, and must be labelled.

Observed data are a separate external-validation layer, not a silent
replacement of the preregistered benchmark. Before making real-market claims,
the project must add a frozen, checksummed extract from a primary source such
as CAISO OASIS and/or CAISO Daily Energy Storage Reports, with:

1. query URL or report identifier;
2. retrieval timestamp and timezone;
3. raw-file checksum;
4. transformation script and units;
5. missing-data and aggregation rules;
6. a clear statement of what remains simulated.

No API key is presently required to test the relaxation theorem, implement
`C_ASSOC`, or run the benchmark runtime pilot. If an API key becomes useful
for the later external-validity layer, it will be requested only after the
exactness/runtime gate passes.

## 4. Stop rule

Data acquisition does not justify continuing a failed instrument. If the
continuous relaxation is not contract-exact and neither deterministic recovery
nor a narrowly defined partial-integrality formulation preserves the frozen
stage-1 contract and independent replay, the large v4 comparison does not run.


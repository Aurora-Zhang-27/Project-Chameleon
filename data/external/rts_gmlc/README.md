# RTS-GMLC source snapshot

Source: NREL/DOE Grid Modernization Lab Consortium, `GridMod/RTS-GMLC`.

Pinned upstream commit:
`3ece0d3725c844056132393ee252b3083dd4eab4`.

The complete upstream README and mandatory data-use disclaimer from that
commit are retained verbatim in `UPSTREAM_README.md`. Any redistributed copy
of these CSV files must keep that notice and credit DOE/NREL/ALLIANCE as
specified there.

The MFE implementation gate uses:

- `gen.csv` for the four fixed thermal-unit records;
- `DAY_AHEAD_regional_Load.csv` for the three-region load sum;
- `DAY_AHEAD_pv.csv` for the aggregate PV shape;
- the two regional flex files and `reserves.csv` only as retained source
  context. The confirmatory MFE reserve tiers are the pre-registered
  percentages of scaled load, not these raw reserve time series.

SHA-256 checksums:

| File | SHA-256 |
|---|---|
| `DAY_AHEAD_pv.csv` | `bfede6e558df5ea0f244b6326940a4ee0b95138643aa8a062897c67134c9c185` |
| `DAY_AHEAD_regional_Flex_Down.csv` | `5c6c2897325a3234865dd62e2321f5f209577c1c30819526b6de516a28e2f967` |
| `DAY_AHEAD_regional_Flex_Up.csv` | `13c03fcf529414d51d744a6c65f151a0ca67765134164114bb080887cae1aa68` |
| `DAY_AHEAD_regional_Load.csv` | `7a9470d32d49068a91334cb36db54cceb2feb5cb1f702b0fa0847af8bac6cf21` |
| `gen.csv` | `988466f29132b73739de60c9204dd4a2a9ceb0adf572e5966c086611272f4068` |
| `reserves.csv` | `3c0d388631b93fe37bc617dc3f9512950927ae1b0a0e878482e90137106d0a28` |

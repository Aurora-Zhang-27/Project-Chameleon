# Retained results

- `affine_samples.csv`: eight historical sample batches by N and power family. The strict unresolved count is samples minus segregated_certified.
- `affine_scaling.csv`: historical median runtimes, separating LP solving, re-solving/certification and model construction. Long-horizon mild batches have no tree-LP comparison.
- `vertex_summary.json`: aggregate lifted-affine vertex screening; floating-point evidence, not rational certificates for every vertex.
- `provenance.json`: local source commit and SHA256 hashes of the original JSON files. Raw research data are outside this minimal publication; retained scripts reproduce the sample-generation procedure.
- `certificates.txt` and `release_checks.json`: exact certificates, regression results and entry-point checks run in the publication worktree.

Historical timings depend on hardware and software versions. High empirical acceptance is not a general exactness theorem; use the certificate scripts for exact counterexamples.

Blank tree_feasible_float cells in `affine_scaling.csv` mean that the tree LP was not run, rather than that no states were feasible.

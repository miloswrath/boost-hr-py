# rust-ols-adherence-cli

Predict unsupervised adherence proportion (y) from supervised adherence proportion (x) using OLS or WLS.

## Install
`cargo build --release`

Binary at `target/release/rust-ols-adherence-cli`.

## Data format (CSV)
Expect columns:
- `sup_prop` — supervised adherence proportion (x in [0,1])
- `unsup_prop` — unsupervised adherence proportion (y in [0,1])
- `unsup_den` — (optional) denominator for unsupervised (e.g., number of sessions observed, ≤ 30)

Example:
```csv
sup_prop,unsup_prop,unsup_den
0.70,0.50,20
0.80,0.62,28
0.40,0.30,12
```
---

## fit a model from csv
```
./rust-ols-adherence-cli fit \
  --csv data.csv \
  --weights binomial \
  --out model.json
```
Weights:

none     → ordinary least squares

n        → w_i = unsup_den

binomial → w_i = unsup_den / (p_i*(1-p_i))  (with p_i clamped to [1e-6, 1-1e-6])









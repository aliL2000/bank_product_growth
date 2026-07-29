# Dataset: Santander Product Recommendation

Source: https://www.kaggle.com/c/santander-product-recommendation

## Download steps
1. Create a free Kaggle account if you don't have one.
2. Go to the competition page above and accept the competition rules (required
   before download is allowed, even though the competition is closed).
3. Download `train_ver2.csv.zip` and `test_ver2.csv.zip` (via the web UI, or the
   Kaggle CLI: `kaggle competitions download -c santander-product-recommendation`).
4. Unzip and place `train_ver2.csv` and `test_ver2.csv` in `data/raw/`.
5. Both files are gitignored — they should never be committed.

## Overview
- Monthly snapshots from **2015-01-28** to **2016-06-28** (17 months) of a customer's
  relationship with the bank.
- ~950,000 unique customers, ~13M+ rows total in `train_ver2.csv`.
- Each row = one customer, one month. 24 profile/behavior columns + 24 binary
  product-ownership flag columns.
- `test_ver2.csv` is the 2016-06-28 snapshot only (used for the original Kaggle
  competition's forward-prediction task — we may or may not use it directly,
  since our framing constructs labels from consecutive months in the train file).

## Profile / behavior columns (partial — fill in from Kaggle data dictionary)
| Column | Description |
|---|---|
| `fecha_dato` | Snapshot date (month) |
| `ncodpers` | Customer ID |
| `ind_empleado` | Employee index (active/ex-employee/etc.) |
| `pais_residencia` | Country of residence |
| `sexo` | Sex |
| `age` | Age |
| `fecha_alta` | Date customer became first holder of a contract |
| `antiguedad` | Customer seniority (months) |
| `nuevocliente` / `ind_nuevo` | New customer index |
| `indrel` | Primary customer indicator |
| `tiprel_1mes` | Customer relationship type at start of month |
| `indresi` | Residence index (same as bank country?) |
| `indext` | Foreigner index |
| `canal_entrada` | Channel used to join |
| `indfall` | Deceased index |
| `tipodom` | Address type |
| `cod_prov` | Province code |
| `nomprov` | Province name |
| `ind_actividad_cliente` | Activity index (active/inactive) |
| `renta` | Gross household income |
| `segmento` | Customer segment (VIP / individuals / college graduated) |

> TODO: complete/verify against the actual Kaggle data dictionary once the file is
> downloaded — some column semantics are ambiguous in the original competition docs
> and worth double-checking against the data itself.

## Product ownership flags (24 binary columns, examples)
- `ind_ahor_fin_ult1` — savings account
- `ind_cco_fin_ult1` — current account
- `ind_cder_fin_ult1` — derivada account
- `ind_ctju_fin_ult1` — junior account
- `ind_ctma_fin_ult1` — más particular account
- `ind_ctop_fin_ult1` — particular account
- `ind_ctpp_fin_ult1` — particular plus account
- `ind_deco_fin_ult1` — short-term deposits
- `ind_deme_fin_ult1` — medium-term deposits
- `ind_dela_fin_ult1` — long-term deposits
- `ind_ecue_fin_ult1` — e-account
- `ind_fond_fin_ult1` — **mutual funds** (Service A candidate)
- `ind_hip_fin_ult1` — mortgage
- `ind_plan_fin_ult1` — pensions plan
- `ind_pres_fin_ult1` — loans
- `ind_reca_fin_ult1` — taxes
- `ind_tjcr_fin_ult1` — **credit card** (Service A candidate)
- `ind_valo_fin_ult1` — securities
- `ind_viv_fin_ult1` — home account
- `ind_nomina_ult1` — **payroll** (Service A candidate)
- `ind_nom_pens_ult1` — payroll pension
- `ind_recibo_ult1` — direct debit

## Label construction (adoption)
For `ind_tjcr_fin_ult1` (Service A, see below):
- Adoption event for customer *c* in month *t* = `ind_tjcr_fin_ult1[c, t-1] == 0`
  and `ind_tjcr_fin_ult1[c, t] == 1`.
- Requires joining each customer's row in month *t* to their row in month *t-1* —
  watch for customers who are new in month *t* (no prior row) and customers who
  churn out entirely (no row in month *t*).

## Service A: credit card (`ind_tjcr_fin_ult1`)
**Decided** — see `docs/decisions/001-service-a-product-choice.md` for full
reasoning. Prevalence across the 17 monthly snapshots (full-file scan) ranges
from ~5.8% (2015 mid-year) down to ~3.7% (by mid-2016) of the customer base
holding a credit card in a given month — a large, non-holder-dominated pool to
target, and a product a bank can plausibly influence via outreach (unlike
payroll, which is more employer-switch-driven).

The two products considered and passed over (payroll account
`ind_nomina_ult1`, mutual funds `ind_fond_fin_ult1`) are documented in the
decision record above for reference.

# Compound Cold Events — UK Analysis Code

Code supporting the analysis of compound cold-dry (CD) and cold-wet (CW) events
across the UK during the extended winter season (December–February), including
their association with large-scale weather regimes.

---

## Repository structure

```
compound_cold_events/
├── notebooks/
│   ├── 01_DJF_extraction.ipynb              # Extract HadUK-Grid data & compute percentiles
│   ├── 02_spatial_maps_DJF_percentiles.ipynb # Spatial maps of thresholds & occurrence
│   ├── 03_cities_analysis.ipynb             # City-level event duration & inter-annual trends
│   └── 04_regime_occurrence_output.ipynb    # Weather-regime attribution maps
├── scripts/
│   ├── map_of_occurrence.py                 # Gridded CD event counts (HPC script)
│   └── run_occurrence.sh                    # SLURM submission script for the above
├── data/           ← not included; see Data section below
├── output/         ← created automatically when scripts run
└── figures/        ← created automatically when notebooks run
```

---

## Data

All observational data are from **HadUK-Grid** (5 km resolution), available
from the CEDA archive:

> https://catalogue.ceda.ac.uk/uuid/4dc8450d889a491ebb20e724debe2dfb

Variables used:
- `tasmin` — daily minimum air temperature
- `rainfall` — daily precipitation

The weather-regime classification used in this study follows the 30-regime
catalogue described in [https://doi.org/10.1002/met.1563].

---

## Running the code

### 1. Configure paths

Each notebook and script has a clearly marked **"User configuration"** section
at the top. Set the `data_dir`, `data_arrays_dir`, and `output_dir` variables
to point to your local data before running.

### 2. Recommended run order

| Step | File | Description |
|------|------|-------------|
| 1 | `notebooks/01_DJF_extraction.ipynb` | Extract raw NetCDF data into NumPy arrays and compute percentile thresholds |
| 2 | `scripts/map_of_occurrence.py` | Compute gridded CD event counts (best submitted via SLURM — see `run_occurrence.sh`) |
| 3 | `notebooks/02_spatial_maps_DJF_percentiles.ipynb` | Spatial maps of thresholds and event occurrence |
| 4 | `notebooks/03_cities_analysis.ipynb` | City-level event statistics |
| 5 | `notebooks/04_regime_occurrence_output.ipynb` | Weather-regime attribution maps |

### 3. HPC / SLURM

`scripts/run_occurrence.sh` submits `map_of_occurrence.py` to a SLURM
scheduler. Edit the `--partition`, `--time`, and `--mem` directives and the
`module add` line to match your HPC environment before submitting:

```bash
sbatch scripts/run_occurrence.sh
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations |
| `pandas` | Tabular data handling |
| `matplotlib` | Plotting |
| `cartopy` | Map projections |
| `netCDF4` | Reading HadUK-Grid files |
| `seaborn` | Distribution plots |

Install with:

```bash
pip install numpy pandas matplotlib cartopy netCDF4 seaborn
```

Python 3.7+ is required (tested with 3.7 on JASMIN HPC).

---

## Notes

- The 30-year climatological baseline used for percentile thresholds spans
  1994–2023 (years at index 34 onward from 1960).
- Precipitation percentiles are computed using wet days only (≥ 0.2 mm),
  following standard WMO practice.
- Non-leap year Februaries are padded with NaN in the 91-day seasonal arrays
  so that all years share the same array shape.

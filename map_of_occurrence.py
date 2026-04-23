"""
map_of_occurrence.py
====================
Computes gridded counts of compound cold-dry (CD) events and the subset of
those events occurring under NAO-negative weather regimes.

For every non-masked grid point the script:
  1. Reads pre-processed monthly arrays of minimum temperature, precipitation,
     time and weather-regime labels.
  2. Applies per-pixel percentile thresholds to identify CD days.
  3. Counts total CD days and CD days that fall under NAO-negative regimes.

Outputs
-------
Two NumPy arrays are saved to DATA_OUT_DIR:
  - CD_total_recent30_newP_filtered.npy   : total CD day count per grid cell
  - CD_NAOneg_recent30_newP_filtered.npy  : NAO-negative CD day count per grid cell

Usage
-----
Run directly or submit via the accompanying run_occurrence.sh SLURM script:
    python map_of_occurrence.py

Configure the paths in the "User configuration" section below before running.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# User configuration
# Edit these paths to match your local data layout.
# ---------------------------------------------------------------------------

# Directory containing the pre-processed monthly .npy arrays
# (e.g. jan_min_temp_all.npy, jan_precip_all.npy, jan_time.npy, jan_WR.npy)
DATA_ARRAYS_DIR = "data/arrays"

# Directory containing the pre-computed percentile .npy files
# (e.g. minT_percentiles_30yr.npy, perc15_percentiles_30yr_filtered.npy)
PERCENTILES_DIR = "data/percentiles"

# Directory where output arrays will be saved
DATA_OUT_DIR = "output/arrays"

# Weather-regime indices that correspond to NAO-negative patterns
# (these are indices into the regime classification used in the original study)
WR_NAO_NEG_INDICES = [6, 9, 11, 19, 25, 27, 28]

# Months forming the extended winter season
MONTHS = ["jan", "feb", "dec"]

# Number of years in the dataset
N_YEARS = 63

# Month lengths (February is treated as 29 days to accommodate leap years;
# missing non-leap days are handled via NaN masking upstream)
MONTH_LENGTHS = {"jan": 31, "feb": 29, "dec": 31, "nov": 30}

# Fill value used for masked / ocean grid cells
FILL_VALUE = 1.0e20

# Grid dimensions [latitude, longitude]
GRID_SHAPE = (290, 180)


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def build_event_df(lat, lon):
    """
    Count total CD events and NAO-negative CD events at a single grid cell.

    Parameters
    ----------
    lat : int
        Latitude index into the grid arrays.
    lon : int
        Longitude index into the grid arrays.

    Returns
    -------
    total : int
        Total number of CD days at this grid cell across all months and years.
    total_NAOneg : int
        Number of those CD days that occur under NAO-negative weather regimes.
    """

    # Quick NaN check using the January temperature array
    temp_test = np.load(f"{DATA_ARRAYS_DIR}/jan_min_temp_all.npy")
    if temp_test[0, 0, lat, lon] == FILL_VALUE:
        return 0, 0

    # Load percentile thresholds for this grid cell
    perc_minT_grid = np.load(f"{PERCENTILES_DIR}/minT_percentiles_30yr.npy")
    perc_prec_grid = np.load(f"{PERCENTILES_DIR}/perc15_percentiles_30yr_filtered.npy")
    perc_minT = perc_minT_grid[lat, lon]
    perc_prec = perc_prec_grid[lat, lon]

    all_months_data = []

    for month in MONTHS:
        month_length = MONTH_LENGTHS[month]

        # Load monthly arrays
        temp    = np.load(f"{DATA_ARRAYS_DIR}/{month}_min_temp_all.npy")
        precip  = np.load(f"{DATA_ARRAYS_DIR}/{month}_precip_all.npy")
        time    = np.load(f"{DATA_ARRAYS_DIR}/{month}_time.npy", allow_pickle=True)
        WR      = np.load(f"{DATA_ARRAYS_DIR}/{month}_WR.npy",   allow_pickle=True)

        # Extract weather-regime values (column 1 of WR array)
        WR_values_1d = WR[:, 1]

        # Extract this grid cell's time series
        gridsquare_temp   = temp[:, :, lat, lon]
        gridsquare_precip = precip[:, :, lat, lon]

        # Binary exceedance flags
        temp_binary   = (gridsquare_temp   <= perc_minT).astype(int)
        precip_binary = (gridsquare_precip <= perc_prec).astype(int)

        # CD flag: both thresholds met simultaneously
        cd_flag = ((temp_binary > 0) & (precip_binary > 0)).astype(int)
        cd_flag[cd_flag > 0] = 3  # retain legacy encoding

        # Reshape time and WR arrays to (N_YEARS, month_length)
        time_2d = np.reshape(time, (N_YEARS, month_length))
        WR_2d   = np.reshape(WR_values_1d, (N_YEARS, month_length))

        # Extract CD event metadata
        compound_event_indices = np.where(cd_flag == 3)
        tmet     = gridsquare_temp[compound_event_indices]
        pmet     = gridsquare_precip[compound_event_indices]
        dmet     = time_2d[compound_event_indices]
        WR_value = WR_2d[compound_event_indices]

        stack = np.column_stack((dmet, tmet, pmet, WR_value))
        all_months_data.append(stack)

    # Combine all months into a single DataFrame
    events_df = pd.DataFrame(np.vstack(all_months_data))

    # Count events under NAO-negative regimes
    WR_counter = [
        len(np.where(events_df[3] == wr_idx)[0])
        for wr_idx in WR_NAO_NEG_INDICES
    ]

    total_NAOneg = int(np.sum(WR_counter))
    total        = len(events_df[3])

    return total, total_NAOneg


# ---------------------------------------------------------------------------
# Main loop — iterate over all non-masked grid cells
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.makedirs(DATA_OUT_DIR, exist_ok=True)

    # Identify non-masked grid cells using the January temperature array
    temp = np.load(f"{DATA_ARRAYS_DIR}/jan_min_temp_all.npy")
    test_mask = temp[0, 0, :, :].copy().astype(float)
    test_mask[test_mask == FILL_VALUE] = np.nan

    valid_indices = np.where(~np.isnan(test_mask))

    # Initialise output arrays
    CD_total  = np.zeros(GRID_SHAPE)
    CD_NAOneg = np.zeros(GRID_SHAPE)

    for i in range(len(valid_indices[0])):
        lat_i = valid_indices[0][i]
        lon_i = valid_indices[1][i]
        print(f"Processing grid cell {i + 1}/{len(valid_indices[0])}  "
              f"(lat_idx={lat_i}, lon_idx={lon_i})")
        CD_total[lat_i, lon_i], CD_NAOneg[lat_i, lon_i] = build_event_df(lat_i, lon_i)

    # Save results
    np.save(f"{DATA_OUT_DIR}/CD_total_recent30_newP_filtered.npy",  CD_total)
    np.save(f"{DATA_OUT_DIR}/CD_NAOneg_recent30_newP_filtered.npy", CD_NAOneg)
    print("Done. Output saved to", DATA_OUT_DIR)

#!/bin/bash
#SBATCH --partition=short-serial
#SBATCH -o map_of_occurrence.out
#SBATCH -e map_of_occurrence.err
#SBATCH --time=24:00:00
#SBATCH --mem=25G

# SLURM submission script for map_of_occurrence.py
# Adjust the module name and script path to match your HPC environment.

module add jaspy/3.7

# Run from the repository root so that relative data paths resolve correctly
cd "$(dirname "$0")/.."
python scripts/map_of_occurrence.py

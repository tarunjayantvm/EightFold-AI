import argparse
import json
from pipeline import run_pipeline

parser = argparse.ArgumentParser(
    description="Multi-Source Candidate Data Transformer — Eightfold AI"
)
parser.add_argument(
    "--inputs", nargs="+", required=True,
    help="Input file paths e.g. data/candidates.csv data/ats_export.json"
)
parser.add_argument(
    "--config", default="config/default_config.json",
    help="Config JSON path"
)
parser.add_argument(
    "--output", default="output/output.json",
    help="Output JSON path"
)

args    = parser.parse_args()
results = run_pipeline(
    input_paths = args.inputs,
    config_path = args.config,
    output_path = args.output
)

print(json.dumps(results, indent=2))
"""Same-input full conversion/replay costs; no numerical solver measurement."""
import argparse
import csv
from fractions import Fraction as F
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from order_verify import replay as upset_replay
from transport_verify import convert, replay as transport_replay
from runtime_support import configure, capabilities, peak_rss_kib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError("evidence must be outside the artifact tree")
    out.mkdir(parents=True, exist_ok=False)
    configure()
    data = json.loads((ROOT / "results/order-certificates.json").read_text("utf-8"))
    records = [(name, record) for name, record in sorted(data["retained"].items())]
    records += [("seed-" + str(r["seed"]), r) for r in data["random"]]
    rows = []
    for name, record in records:
        raw_task = json.dumps(record["task"], separators=(",", ":"))
        raw_proof = json.dumps(record["certificate"], separators=(",", ":"))
        for repeat in range(3):
            # Alternate order to avoid assigning every warm-cache benefit to one
            # route. Both consume the identical serialized task and source proof.
            methods = ("upsets", "conversion+transport") if repeat % 2 == 0 else ("conversion+transport", "upsets")
            for method in methods:
                cpu, wall = time.process_time_ns(), time.perf_counter_ns()
                task, cert = json.loads(raw_task), json.loads(raw_proof)
                if method == "upsets":
                    value = upset_replay(task, cert)
                    destination_bytes = len(raw_proof.encode("utf-8"))
                else:
                    destination = convert(task, cert)  # includes its acceptance replay
                    encoded = json.dumps(destination, separators=(",", ":"))
                    value = transport_replay(task, json.loads(encoded))
                    destination_bytes = len(encoded.encode("utf-8"))
                elapsed_wall = time.perf_counter_ns() - wall
                elapsed_cpu = time.process_time_ns() - cpu
                if value != F(record["value"]):
                    raise RuntimeError("same-information objective disagreement")
                rows.append({"case": name, "repeat": repeat, "method": method, "value": str(value),
                             "wall_ns": elapsed_wall, "cpu_ns": elapsed_cpu,
                             "source_bytes": len(raw_proof.encode("utf-8")), "destination_bytes": destination_bytes})
        compact = convert(record["task"], record["certificate"])
        (out / (name + ".json")).write_text(json.dumps({"task": record["task"],
            "source_certificate": record["certificate"], "transport_certificate": compact}, indent=2) + "\n", "utf-8")
    with (out / "costs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    ratios = []
    for name, _ in records:
        times = {method: statistics.median(r["wall_ns"] for r in rows if r["case"] == name and r["method"] == method)
                 for method in ("upsets", "conversion+transport")}
        ratios.append(times["conversion+transport"] / times["upsets"])
    record = {"tasks": len(records), "repeats": 3, "measurement_rows": len(rows),
              "objective_mismatches": 0, "median_full_cost_ratio_transport_over_upsets": statistics.median(ratios),
              "transport_faster_tasks": sum(r < 1 for r in ratios),
              "scope": "same 24 retained tasks; parse+convert+serialize+two exact destination replays versus parse+upset replay; LP production excluded on both sides",
              "representation": "destination has dense transport plus 2*k*d signed potentials; conversion still enumerates upward sets",
              "python": sys.version, "os": platform.platform(), "optimize": sys.flags.optimize,
              "resource_capabilities": capabilities(), "peak_process_rss_kib": peak_rss_kib()}
    (out / "receipt.json").write_text(json.dumps(record, indent=2) + "\n", "utf-8")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()

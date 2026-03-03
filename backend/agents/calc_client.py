"""HTTP client for the HyperFormula calculation engine."""

import os
import urllib.request
import urllib.error
import json
from typing import Any, Optional

CALC_ENGINE_URL = os.getenv("CALC_ENGINE_URL", "http://localhost:4100")


def _post(path: str, body: dict) -> dict:
    url = f"{CALC_ENGINE_URL}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"CalcEngine {path} failed ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"CalcEngine unavailable at {CALC_ENGINE_URL}: {e.reason}. "
            "Is the calc-engine service running?"
        )


def _get(path: str) -> dict:
    url = f"{CALC_ENGINE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"status": "unreachable"}


def health() -> dict:
    return _get("/health")


def is_available() -> bool:
    try:
        h = health()
        return h.get("status") == "ok"
    except Exception:
        return False


def load_model(sheets: list[dict]) -> dict:
    """Load sheet data into the calc engine.

    Args:
        sheets: List of {"name": str, "data": 2D array} dicts.
    """
    return _post("/load", {"sheets": sheets})


def calculate(
    sets: list[dict],
    reads: list[dict],
) -> list[dict]:
    """Set cells temporarily, read results, restore originals.

    Args:
        sets: [{"sheet", "col", "row", "value"}, ...]
        reads: [{"sheet", "col", "row"}, ...]

    Returns:
        List of {"sheet", "col", "row", "value"} results.
    """
    resp = _post("/calculate", {"sets": sets, "reads": reads})
    return resp.get("results", [])


def optimize(
    levers: list[dict],
    objective: dict,
    targets: Optional[list[dict]] = None,
    direction: str = "maximize",
    samples: int = 500,
    top_n: int = 5,
    extra_reads: Optional[list[dict]] = None,
) -> dict:
    """Run the optimizer over lever ranges to find solutions.

    Args:
        levers: [{"sheet", "col", "row", "min", "max", "label"}, ...]
        objective: {"sheet", "col", "row", "label"}
        targets: [{"sheet", "col", "row", "operator", "value", "label"}, ...]
        direction: "maximize" or "minimize"
        samples: Number of Latin hypercube samples
        top_n: Number of top solutions to return
        extra_reads: Additional cells to read in each solution

    Returns:
        {"solutions": [...], "totalSampled": N, "feasibleCount": N, "elapsed_ms": N}
    """
    body: dict[str, Any] = {
        "levers": levers,
        "objective": objective,
        "direction": direction,
        "samples": samples,
        "topN": top_n,
    }
    if targets:
        body["targets"] = targets
    if extra_reads:
        body["extraReads"] = extra_reads

    return _post("/optimize", body)

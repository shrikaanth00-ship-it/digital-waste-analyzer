# estimator.py
# Heuristic estimator for runtime and complexity based on AST findings.
from typing import List, Dict, Any

# Default assumptions (configurable)
DEFAULT_LIST_SIZE = 100   # assumed size when unknown
BASE_OP_COST = 1e-6       # seconds per simple operation (very small baseline)


def estimate_block_runtime(findings: List[Dict[str, Any]]) -> float:
    """
    Given rule findings (from rules.get_findings), produce an estimated runtime (seconds)
    for a single run of the script using simple heuristics.
    Returns estimated seconds.
    """
    sec = 0.0

    # baseline per-file overhead
    sec += 0.0001

    for f in findings:
        rid = f.get("rule_id")
        sev = f.get("severity")
        # severity weight to scale impact
        weight = {"low": 0.5, "medium": 1.0, "high": 2.0}.get(sev, 1.0)

        # heuristic impacts per rule id (very approximate)
        if rid == "R001":  # nested loops
            # assume nested loop over DEFAULT_LIST_SIZE -> O(n^2)
            impact = BASE_OP_COST * (DEFAULT_LIST_SIZE ** 2) * weight
        elif rid == "R002":  # expensive call in loop
            impact = BASE_OP_COST * DEFAULT_LIST_SIZE * 10.0 * weight
        elif rid == "R003":  # membership-in-list
            impact = BASE_OP_COST * DEFAULT_LIST_SIZE * 2.0 * weight
        elif rid == "R004":  # string concat in loop
            impact = BASE_OP_COST * DEFAULT_LIST_SIZE * 1.5 * weight
        elif rid == "R005":  # file I/O in loop
            # I/O is heavier — assume 0.0005s per op
            impact = 0.0005 * DEFAULT_LIST_SIZE * weight
        elif rid == "R006":  # unused imports
            impact = 0.00001 * weight
        else:
            impact = BASE_OP_COST * DEFAULT_LIST_SIZE * weight

        sec += impact

    # clamp minimum
    if sec < 1e-6:
        sec = 1e-6
    return sec


def complexity_score(findings: List[Dict[str, Any]]) -> float:
    """
    Return a 0..100 complexity-ish score (higher = worse).
    Simple mapping: more & higher severity findings => higher complexity.
    """
    score = 0.0
    for f in findings:
        sev = f.get("severity")
        if sev == "low":
            score += 3
        elif sev == "medium":
            score += 8
        elif sev == "high":
            score += 18
    # normalize to 0..100
    if score > 100:
        score = 100.0
    return score

# suggester.py
# Small templated suggestion engine + naive patcher (text-based)
from typing import List, Dict


TEMPLATED_SNIPPETS = {
    "R001": {
        "title": "Avoid nested loops where possible",
        "suggestion": ("Consider using hashing (set/dict) to reduce nested iteration. "
                       "Example:\n\n# before\nfor a in list1:\n    for b in list2:\n        if a == b:\n            do_something()\n\n# after\nset2 = set(list2)\nfor a in list1:\n    if a in set2:\n        do_something()"),
    },
    "R002": {
        "title": "Move expensive calls out of loops or memoize",
        "suggestion": ("If a function call returns the same output each loop, compute it once.\n"
                       "Example:\n\n# before\nfor x in items:\n    val = expensive()\n    use(val)\n\n# after\nval = expensive()\nfor x in items:\n    use(val)"),
    },
    "R003": {
        "title": "Use set for membership checks",
        "suggestion": ("Converting lists to sets makes membership tests O(1) instead of O(n).\n"
                       "Example:\n\ns = set(mylist)\nif x in s:\n    ..."),
    },
    "R004": {
        "title": "Avoid string '+' concatenation in loops",
        "suggestion": ("Collect strings and join them once:\n\nparts = []\nfor x in items:\n    parts.append(str(x))\ntext = ''.join(parts)"),
    },
    "R005": {
        "title": "Avoid file I/O in loops",
        "suggestion": ("Open files once and write in buffered mode:\n\nwith open('out.txt','w') as f:\n    for item in items:\n        f.write(str(item) + '\\n')"),
    },
    "R006": {
        "title": "Remove unused imports",
        "suggestion": ("Unused imports increase load time; remove them to keep code clean."),
    }
}


def generate_suggestions(findings: List[Dict]) -> List[Dict]:
    """
    Map each finding to a suggestion template. Returns list of dicts with
    rule_id, title, suggestion, lineno.
    """
    out = []
    seen = set()
    for f in findings:
        rid = f.get("rule_id")
        if rid in TEMPLATED_SNIPPETS and rid not in seen:
            info = TEMPLATED_SNIPPETS[rid]
            out.append({
                "rule_id": rid,
                "lineno": f.get("lineno"),
                "title": info["title"],
                "suggestion": info["suggestion"],
                "message": f.get("message"),
            })
            seen.add(rid)
    return out


def naive_apply_patch(source: str, findings: List[Dict]) -> str:
    """
    Very naive text-based patcher: applies simple transformations for a few rules.
    This is intentionally conservative and only performs textbook replacements:
      - string concatenation in loops -> join pattern (best-effort)
      - membership-in-list -> add comment recommending set
    It returns a new source string. For safety, it never removes code automatically.
    """
    lines = source.splitlines()
    out_lines = lines.copy()

    for f in findings:
        rid = f.get("rule_id")
        ln = f.get("lineno")
        if not ln:
            continue
        idx = ln - 1
        # R003: membership-in-list -> add comment to convert to set
        if rid == "R003":
            # insert a comment above the line
            if 0 <= idx < len(out_lines):
                out_lines.insert(idx, "# SUGGESTION: Convert container to set for faster membership checks")
        # R004: string concat in loop -> add comment with join suggestion
        if rid == "R004":
            if 0 <= idx < len(out_lines):
                out_lines.insert(idx, "# SUGGESTION: Consider collecting strings and using ''.join(list_of_parts)")
        # R005: file I/O in loop -> suggest opening file outside loop
        if rid == "R005":
            if 0 <= idx < len(out_lines):
                out_lines.insert(idx, "# SUGGESTION: Open file outside the loop and buffer writes")

    return "\n".join(out_lines)

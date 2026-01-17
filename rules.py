# rules.py
# Rule engine skeleton for detecting digital-waste anti-patterns.
# Uses parser.py for AST extraction.

import ast
from typing import List, Dict, Any, Tuple
from parser import CodeParser


class RuleFinding:
    def __init__(self, rule_id: str, severity: str, lineno: int, snippet: str, message: str, suggestion: str):
        self.rule_id = rule_id
        self.severity = severity  # "low", "medium", "high"
        self.lineno = lineno
        self.snippet = snippet
        self.message = message
        self.suggestion = suggestion

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "lineno": self.lineno,
            "snippet": self.snippet,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class RuleEngine:
    def __init__(self, source: str):
        self.parser = CodeParser(source)
        if self.parser.syntax_error:
            self.findings = [{
                "rule_id": "SYNTAX_ERROR",
                "severity": "high",
                "lineno": None,
                "message": "Invalid Python syntax detected",
                "snippet": self.parser.syntax_error,
                "suggestion": "Please fix syntax errors before analysis."
            }]
    return

        self.findings: List[RuleFinding] = []
        self._run_all()

    def _run_all(self):
        self._rule_nested_loops()
        self._rule_expensive_call_in_loop()
        self._rule_membership_in_list()
        self._rule_string_concat_in_loop()
        self._rule_file_io_in_loop()
        self._rule_unused_imports()

    def _rule_nested_loops(self):
        # Detect nested For nodes
        for for_node in self.parser.get_for_loops():
            for child in ast.walk(for_node):
                if child is not for_node and isinstance(child, ast.For):
                    lineno = getattr(for_node, "lineno", None)
                    snippet = self.parser._get_line(for_node)
                    msg = "Nested loop detected; may indicate O(n^2) complexity."
                    suggestion = "Consider using sets/dicts or rethinking algorithm to avoid nested iteration."
                    self.findings.append(RuleFinding("R001", "high", lineno, snippet, msg, suggestion))

    def _rule_expensive_call_in_loop(self):
        # If loop body contains calls to named functions without being dependent on loop vars -> warn
        for for_node in self.parser.get_for_loops():
            calls = [n for n in ast.walk(for_node) if isinstance(n, ast.Call)]
            for c in calls:
                name = self.parser._get_call_name(c)
                # heuristics: open/read/write or user-defined calls (Name), and not using loop var as arg
                if name and name not in ("len", "range", "enumerate", "sum"):
                    # further heuristics: if call's lineno differs from loop header, report
                    lineno = getattr(c, "lineno", None)
                    snippet = self.parser._get_line(c)
                    msg = f"Function call `{name}` inside loop may be expensive if it does heavy work."
                    suggestion = f"Move `{name}` outside loop if possible, or memoize its result."
                    self.findings.append(RuleFinding("R002", "medium", lineno, snippet, msg, suggestion))

    def _rule_membership_in_list(self):
        # finds 'if x in some_list' constructs
        for node in ast.walk(self.parser.tree):
            if isinstance(node, ast.If):
                # check test for 'in' operator
                test = node.test
                if isinstance(test, ast.Compare):
                    for op in test.ops:
                        if isinstance(op, ast.In):
                            lineno = getattr(node, "lineno", None)
                            snippet = self.parser._get_line(node)
                            msg = "Membership test on a list is O(n); consider using a set for faster lookups."
                            suggestion = "Convert the container to a set if membership checks are frequent: `s = set(mylist)`."
                            self.findings.append(RuleFinding("R003", "medium", lineno, snippet, msg, suggestion))

    def _rule_string_concat_in_loop(self):
        # Search for string concatenation patterns inside loops
        for for_node in self.parser.get_for_loops():
            for child in ast.walk(for_node):
                if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                    lineno = getattr(child, "lineno", None)
                    snippet = self.parser._get_line(child)
                    msg = "String concatenation inside loop may be inefficient; use join or StringIO."
                    suggestion = "Collect strings and use `''.join(list_of_parts)` or `io.StringIO`."
                    self.findings.append(RuleFinding("R004", "low", lineno, snippet, msg, suggestion))

    def _rule_file_io_in_loop(self):
        # detect open/write/read inside loops
        for for_node in self.parser.get_for_loops():
            for child in ast.walk(for_node):
                if isinstance(child, ast.Call):
                    name = self.parser._get_call_name(child)
                    if name in ("open", "write", "writelines"):
                        lineno = getattr(child, "lineno", None)
                        snippet = self.parser._get_line(child)
                        msg = "File I/O inside loop detected. This can be slow and energy-intensive."
                        suggestion = "Open files once outside the loop and buffer writes."
                        self.findings.append(RuleFinding("R005", "high", lineno, snippet, msg, suggestion))

    def _rule_unused_imports(self):
        # simple heuristic: import names that are not used anywhere
        imports = self.parser.get_imports()
        used_names = {n.id for n in ast.walk(self.parser.tree) if isinstance(n, ast.Name)}
        for imp in imports:
            # get alias or module name
            if isinstance(imp, ast.Import):
                for name in imp.names:
                    if name.asname:
                        nm = name.asname
                    else:
                        nm = name.name.split('.')[0]
                    if nm not in used_names:
                        lineno = getattr(imp, "lineno", None)
                        snippet = self.parser._get_line(imp)
                        msg = f"Import `{nm}` appears unused."
                        suggestion = "Remove unused imports to reduce code bloat."
                        self.findings.append(RuleFinding("R006", "low", lineno, snippet, msg, suggestion))
            elif isinstance(imp, ast.ImportFrom):
                module = imp.module or ""
                for name in imp.names:
                    nm = name.asname or name.name
                    if nm not in used_names:
                        lineno = getattr(imp, "lineno", None)
                        snippet = self.parser._get_line(imp)
                        msg = f"Import from `{module}` appears unused."
                        suggestion = "Remove unused imports to reduce code bloat."
                        self.findings.append(RuleFinding("R006", "low", lineno, snippet, msg, suggestion))

    def get_findings(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.findings]


if __name__ == "__main__":
    demo = '''
import os, json

def report(items, other):
    s = ""
    for x in items:
        if x in other:
            s += str(x)
    for a in items:
        for b in items:
            pass
    f = open("out.txt", "w")
    f.write("ok")
'''
    engine = RuleEngine(demo)
    for f in engine.get_findings():
        print(f)


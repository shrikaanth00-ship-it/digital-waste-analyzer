# parser.py
# Simple AST helpers to parse python code and extract nodes of interest.

import ast
from typing import List, Tuple, Dict, Any


class CodeParser:
      def __init__(self, source: str):
        self.source = source
        self.tree = None
        self.syntax_error = None

        try:
            self.tree = ast.parse(source)
        except SyntaxError as e:
            self.syntax_error = str(e)

    def get_functions(self) -> List[ast.FunctionDef]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]

    def get_for_loops(self) -> List[ast.For]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.For)]

    def get_while_loops(self) -> List[ast.While]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.While)]

    def get_calls(self) -> List[ast.Call]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)]

    def get_imports(self) -> List[ast.Import]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.Import)] + \
               [n for n in ast.walk(self.tree) if isinstance(n, ast.ImportFrom)]

    def get_list_comprehensions(self) -> List[ast.comprehension]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.comprehension)]

    def get_string_concat_ops(self) -> List[Tuple[int, str]]:
        """Detect '+' operations between strings in AST (simple heuristic)."""
        results = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                # crude check: any BinOp with string constants or names used as concatenation
                left_is_str = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
                right_is_str = isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)
                if left_is_str or right_is_str:
                    results.append((getattr(node, 'lineno', None), self._get_line(node)))
        return results

    def get_file_io_calls(self) -> List[Tuple[int, str]]:
        """Detect open()/read()/write() calls by name (simple heuristic)."""
        hits = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                fname = self._get_call_name(node)
                if fname in ("open", "read", "write", "writelines"):
                    hits.append((getattr(node, 'lineno', None), self._get_line(node)))
        return hits

    def _get_call_name(self, call: ast.Call) -> str:
        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            return call.func.attr
        return ""

    def _get_line(self, node: ast.AST) -> str:
        ln = getattr(node, "lineno", None)
        if ln and 1 <= ln <= len(self.lines):
            return self.lines[ln - 1].strip()
        return ""

    def get_all_nodes_with_context(self) -> List[Dict[str, Any]]:
        """Return summary of major nodes with lineno and snippets for rule engine."""
        nodes = []
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.For, ast.While, ast.FunctionDef, ast.Call, ast.Import, ast.ImportFrom)):
                nodes.append({
                    "type": type(n).__name__,
                    "lineno": getattr(n, "lineno", None),
                    "col_offset": getattr(n, "col_offset", None),
                    "snippet": self._get_line(n)
                })
        return nodes


if __name__ == "__main__":
    # quick demo
    sample = '''
import os
def foo(arr, lst):
    out = ""
    for x in arr:
        if x in lst:
            out += str(x)
    for i in range(len(arr)):
        for j in range(len(arr)):
            pass
    f = open("data.txt", "w")
    f.write("hello")
'''
    p = CodeParser(sample)
    print("Functions:", [f.name for f in p.get_functions()])
    print("For-loops:", [(n.lineno, p._get_line(n)) for n in p.get_for_loops()])
    print("File I/O calls:", p.get_file_io_calls())


# parser.py
import ast
from typing import List, Dict, Any

class CodeParser:
    def __init__(self, source: str):
        self.source = source or ""
        self.tree = None
        self.syntax_error = None
        self.lines = self.source.splitlines()
        try:
            # parse source into AST
            self.tree = ast.parse(self.source)
        except SyntaxError as e:
            # store syntax error string for the caller to show
            self.syntax_error = f"{e.msg} (line {e.lineno})"

    def get_functions(self) -> List[ast.FunctionDef]:
        if self.tree is None:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]

    def get_for_loops(self) -> List[ast.For]:
        if self.tree is None:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.For)]

    def get_while_loops(self) -> List[ast.While]:
        if self.tree is None:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.While)]

    def get_calls(self) -> List[ast.Call]:
        if self.tree is None:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)]

    def get_imports(self) -> List[Any]:
        if self.tree is None:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, (ast.Import, ast.ImportFrom))]

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

    def get_file_io_calls(self) -> List[Dict[str, Any]]:
        hits = []
        if self.tree is None:
            return hits
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name in ("open", "read", "write", "writelines"):
                    hits.append({"lineno": getattr(node, "lineno", None), "snippet": self._get_line(node)})
        return hits

    def get_all_nodes_with_context(self) -> List[Dict[str, Any]]:
        nodes = []
        if self.tree is None:
            return nodes
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.For, ast.While, ast.FunctionDef, ast.Call, ast.Import, ast.ImportFrom)):
                nodes.append({
                    "type": type(n).__name__,
                    "lineno": getattr(n, "lineno", None),
                    "col_offset": getattr(n, "col_offset", None),
                    "snippet": self._get_line(n)
                })
        return nodes

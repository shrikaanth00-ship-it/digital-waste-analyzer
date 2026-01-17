from rules import RuleEngine

code = """
import os
for i in range(10):
    for j in range(10):
        pass
"""

engine = RuleEngine(code)
for f in engine.get_findings():
    print(f)

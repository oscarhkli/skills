#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
if args[:2] != ["pr", "list"] or "--head" not in args:
    sys.exit(0)
head = args[args.index("--head") + 1]
prs = json.loads((Path(__file__).parent / "prs.json").read_text()).get(head, [])
if "--json" in args:
    fields = args[args.index("--json") + 1].split(",")
    prs = [{k: p[k] for k in fields if k in p} for p in prs]
print(json.dumps(prs))

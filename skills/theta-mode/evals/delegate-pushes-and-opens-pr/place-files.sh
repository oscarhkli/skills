#!/usr/bin/env bash
set -eu
python3 "$(dirname "$0")/../fixture.py" install
python3 "$(dirname "$0")/../fixture.py" repo eval-widgets
mkdir -p eval-widgets/docs/plans
printf '# Plan: fix the typo\n\n## Goal\n\nFix the typo gird in README.md.\n\n## Steps\n\n1. Replace gird with grid in README.md.\n' > eval-widgets/docs/plans/fix-typo.md

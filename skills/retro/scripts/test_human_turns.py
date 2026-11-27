import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "human_turns.py"
FIXTURE = ROOT / "evals" / "files" / "projects" / "demo" / "2222bbbb-hotfix-notes.jsonl"


class HumanTurnsTest(unittest.TestCase):
    def setUp(self):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), str(FIXTURE)],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        self.turns = [re.fullmatch(r"#(\d+) L(\d+): (.*)", line).groups() for line in result.stdout.splitlines()]

    def test_lists_exactly_four_turns_with_one_based_line_numbers(self):
        self.assertEqual([(n, line) for n, line, _ in self.turns], [("1", "2"), ("2", "6"), ("3", "9"), ("4", "10")])

    def test_queued_human_turns_carry_their_prompt(self):
        self.assertEqual(self.turns[2][2], "Also drop the Known issues section.")
        self.assertEqual(self.turns[3][2], "Keep the Owners section.")

    def test_skips_notification_unmarked_and_list_prompts(self):
        lines = {line for _, line, _ in self.turns}
        self.assertFalse(lines & {"8", "11", "12"})


if __name__ == "__main__":
    unittest.main()

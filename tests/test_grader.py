"""Teacher self-checks: accepting correct C is not enough; bad submissions must fail."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_homework import grade, select_pr_sources  # noqa: E402


class GradingTests(unittest.TestCase):
    def check_program(self, code, expected, timeout=3):
        with tempfile.TemporaryDirectory(prefix="grader-fixture-") as directory:
            source = Path(directory) / "clamp_speed.c"
            source.write_text(code, encoding="utf-8")
            result = grade(source, os.environ.get("CC", "gcc"), timeout)
            self.assertEqual(result.status, expected, result.detail)

    def test_correct_solution(self):
        self.check_program(
            "int clamp_speed(int x) { if (x > 1000) return 1000; "
            "if (x < -1000) return -1000; return x; }\n", "PASS")

    def test_wrong_answer(self):
        self.check_program("int clamp_speed(int x) { return x; }\n", "WRONG_ANSWER")

    def test_off_by_one(self):
        self.check_program(
            "int clamp_speed(int x) { if (x > 999) return 999; "
            "if (x < -1000) return -1000; return x; }\n", "WRONG_ANSWER")

    def test_compile_error(self):
        self.check_program("int clamp_speed(int x) { return x }\n", "COMPILE_ERROR")

    def test_unexpected_main(self):
        self.check_program(
            "int main(void) {return 0;} int clamp_speed(int x) {return x;}\n", "COMPILE_ERROR")

    def test_signal_termination(self):
        self.check_program(
            "#include <signal.h>\nint clamp_speed(int x) {(void)x; raise(SIGTERM); return 0;}\n",
            "RUNTIME_ERROR")

    def test_early_exit_is_not_success(self):
        self.check_program(
            "#include <stdlib.h>\nint clamp_speed(int x) {(void)x; exit(0);}\n", "WRONG_ANSWER")

    def test_infinite_loop(self):
        self.check_program(
            "int clamp_speed(int x) {(void)x; for (;;) {} return 0;}\n", "TIMEOUT", 0.3)


class SubmissionTests(unittest.TestCase):
    def test_new_and_updated_student_file(self):
        for status in ("A", "M"):
            self.assertEqual(select_pr_sources([(status, "submissions/Alice/clamp_speed.c")], "alice"),
                             (["submissions/Alice/clamp_speed.c"], False))

    def test_reject_invalid_prs(self):
        for changes in [
            [], [("A", "clamp_speed.c")], [("A", "submissions/alice/main.c")],
            [("A", "submissions/bob/clamp_speed.c")],
            [("D", "submissions/alice/clamp_speed.c")],
            [("T", "submissions/alice/clamp_speed.c")],
            [("A", "submissions/alice/clamp_speed.c"), ("M", "tests/test_clamp_speed.c")],
            [("A", "submissions/alice/clamp_speed.c"), ("A", "submissions/bob/clamp_speed.c")],
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                select_pr_sources(changes, "alice")

    def test_maintenance_pr_is_distinct(self):
        self.assertEqual(select_pr_sources([("M", "README.md")], "teacher"), ([], True))


if __name__ == "__main__":
    unittest.main()

"""Compile and grade homework 01 with the same commands locally and in Actions."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "test_clamp_speed.c"
SUBMISSION = re.compile(r"submissions/([A-Za-z0-9][A-Za-z0-9-]{0,38})/clamp_speed\.c")
MAINTENANCE_FILES = {
    "README.md", ".gitignore", ".github/workflows/c-homework.yml",
    ".github/pull_request_template.md", "assignments/01_clamp_speed/template.c",
    "scripts/check_homework.py", "tests/test_clamp_speed.c", "tests/test_grader.py",
    "submissions/.gitkeep",
}


@dataclass
class Result:
    status: str
    detail: str


def grade(source: Path, compiler: str, run_timeout: float = 3.0) -> Result:
    """One source plus the teacher's main(); no shell or shared executable names."""
    source = source.resolve()
    if not source.is_file() or source.suffix != ".c":
        return Result("INVALID_FILE", "Expected an existing .c file")
    if source.stat().st_size > 65536:
        return Result("INVALID_FILE", "Source must be at most 64 KiB")
    with tempfile.TemporaryDirectory(prefix="c-homework-") as build_dir:
        executable = Path(build_dir) / ("test.exe" if os.name == "nt" else "test")
        command = [
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            str(source), str(HARNESS), "-o", str(executable),
        ]
        try:
            built = subprocess.run(
                command, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=30,
            )
        except subprocess.TimeoutExpired:
            return Result("COMPILE_TIMEOUT", "Compilation exceeded 30 seconds")
        except OSError as error:
            return Result("COMPILER_ERROR", str(error))
        if built.returncode != 0:
            return Result("COMPILE_ERROR", built.stdout + built.stderr)
        try:
            ran = subprocess.run(
                [str(executable)], cwd=build_dir, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=run_timeout,
            )
        except subprocess.TimeoutExpired:
            return Result("TIMEOUT", f"Program exceeded {run_timeout:g} seconds")
        except OSError as error:
            return Result("RUNTIME_ERROR", str(error))
        if ran.returncode != 0:
            status = "WRONG_ANSWER" if ran.stdout.startswith("FAIL:") else "RUNTIME_ERROR"
            return Result(status, f"Exit code {ran.returncode}\n{ran.stdout}{ran.stderr}")
        if ran.stdout.strip() != "PASS: 4016 cases" or ran.stderr.strip():
            return Result("WRONG_ANSWER", "Test did not complete normally, or produced extra output")
        return Result("PASS", "4016 / 4016 cases passed")


def select_pr_sources(changes: list[tuple[str, str]], author: str) -> tuple[list[str], bool]:
    """Student PR: exactly their own .c file. Infrastructure: separate maintenance PR."""
    if not changes:
        raise ValueError("PR has no changed files")
    homework = [(status, path) for status, path in changes if SUBMISSION.fullmatch(path)]
    if homework:
        if len(changes) != 1:
            raise ValueError("Submit only submissions/<GitHub-username>/clamp_speed.c")
        status, path = homework[0]
        if status not in {"A", "M"}:
            raise ValueError("Do not delete, rename or replace a homework file with a symlink")
        if SUBMISSION.fullmatch(path).group(1).lower() != author.lower():
            raise ValueError("Submission directory must match the PR author's GitHub username")
        return [path], False
    if all(path in MAINTENANCE_FILES for _, path in changes):
        return [], True
    raise ValueError("No valid homework: use submissions/<GitHub-username>/clamp_speed.c")


def checked_path(relative: str) -> Path:
    path = ROOT / relative
    if not SUBMISSION.fullmatch(relative):
        raise ValueError(f"Invalid submission path: {relative}")
    if any(part.is_symlink() for part in [path, path.parent, path.parent.parent]):
        raise ValueError(f"Symlinks are not accepted: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Missing or invalid file: {relative}")
    return path


def all_sources() -> list[Path]:
    result = []
    for path in sorted((ROOT / "submissions").rglob("*")):
        if path.name == ".gitkeep":
            continue
        if path.is_file() or path.is_symlink():
            result.append(checked_path(path.relative_to(ROOT).as_posix()))
    return result


def ci_sources() -> tuple[list[Path], str]:
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return all_sources(), "All merged submissions"
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    base = event["pull_request"]["base"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("Invalid PR base commit SHA")
    diff = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", "-z", base, "HEAD", "--"],
        cwd=ROOT, capture_output=True, check=True, timeout=30,
    ).stdout.decode("utf-8").rstrip("\0").split("\0")
    changes = list(zip(diff[0::2], diff[1::2])) if diff != [""] else []
    paths, maintenance = select_pr_sources(changes, event["pull_request"]["user"]["login"])
    if maintenance:
        return all_sources(), "Teaching infrastructure PR (not a student submission)"
    return [checked_path(path) for path in paths], "Student PR"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ci", action="store_true", help="Read GitHub PR event metadata")
    mode.add_argument("--all", action="store_true", help="Test all submissions independently")
    parser.add_argument("--cc", default=os.environ.get("CC", "gcc"), help="C compiler path")
    parser.add_argument("sources", nargs="*", type=Path)
    args = parser.parse_args()
    if args.sources and (args.ci or args.all):
        parser.error("Use explicit source paths OR --ci/--all")
    summary = ["## C homework / grade", ""]
    try:
        if args.ci:
            sources, description = ci_sources()
        elif args.all:
            sources, description = all_sources(), "All submissions"
        elif args.sources:
            sources, description = args.sources, "Local check"
        else:
            parser.error("Provide a .c file, --ci, or --all")
        print(description)
        summary.append(description + "\n")
        if not sources:
            message = "No student submissions yet. Infrastructure checks only. / 当前没有学员作业。"
            print(message)
            summary.append(message)
        failures = 0
        for source in sources:
            result = grade(source, args.cc)
            print(f"[{result.status}] {source}\n{result.detail}", flush=True)
            summary.append(f"- `{source.name}` ({source.parent.name}): **{result.status}**")
            failures += result.status != "PASS"
        return 1 if failures else 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        summary.append(f"Submission validation failed: {error}")
        return 1
    finally:
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
                output.write("\n".join(summary) + "\n")


if __name__ == "__main__":
    sys.exit(main())

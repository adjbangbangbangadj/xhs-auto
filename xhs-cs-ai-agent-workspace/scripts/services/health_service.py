import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class HealthResult:
    passed: bool
    output: str


def run_smoke_tests() -> HealthResult:
    result = subprocess.run(
        [sys.executable, "scripts/run_smoke_tests.py"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    return HealthResult(
        passed=result.returncode == 0,
        output=(result.stdout + "\n" + result.stderr).strip(),
    )

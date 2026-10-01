"""Traceability checks (REQ-14): the matrix must always match the code.

The traceability matrix (docs/06_Traceability_Matrix.md) is written by hand,
because the verification LEVEL and STATUS of a requirement need human judgment.
But the LIST of tests per requirement is a fact that can be read from the code
(@pytest.mark.requirement tags). These tests compare both, so the matrix can
never silently drift away from the test suite again.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Mandatory requirements that are knowingly not covered yet, and why.
KNOWN_UNCOVERED = {
    "REQ-03",   # camera range: needs a real camera detector (step 12)
}


def _tagged_tests() -> dict[str, set[str]]:
    """{REQ-ID: {"test_file::test_name", ...}} read from the requirement tags."""
    tags: dict[str, set[str]] = {}
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for deco in node.decorator_list:
                for req in re.findall(r"requirement\(['\"](REQ-\d+)['\"]\)", ast.unparse(deco)):
                    tags.setdefault(req, set()).add(f"{path.stem}::{node.name}")
    return tags


def _matrix_tests() -> dict[str, set[str]]:
    """{REQ-ID: {"test_file::test_name", ...}} as listed in the matrix table."""
    text = (ROOT / "docs" / "06_Traceability_Matrix.md").read_text(encoding="utf-8")
    rows: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = re.match(r"\|\s*(REQ-\d+)\s*\|", line)
        if match:
            rows[match.group(1)] = set(re.findall(r"`(test_\w+::test_\w+)`", line))
    return rows


def _mandatory_requirements() -> set[str]:
    """IDs of the "Muss" requirements in the requirements specification."""
    text = (ROOT / "docs" / "01_Requirements.md").read_text(encoding="utf-8")
    return set(re.findall(r"^\|\s*(REQ-\d+)\s*\|.*\|\s*Muss\s*\|\s*$", text, flags=re.MULTILINE))


@pytest.mark.requirement("REQ-14")
def test_matrix_lists_exactly_the_tagged_tests():
    tagged, matrix = _tagged_tests(), _matrix_tests()
    problems = []
    for req in sorted(set(tagged) | set(matrix), key=lambda r: int(r.split("-")[1])):
        in_code, in_doc = tagged.get(req, set()), matrix.get(req, set())
        for test in sorted(in_code - in_doc):
            problems.append(f"{req}: tagged in code, missing in matrix -> {test}")
        for test in sorted(in_doc - in_code):
            problems.append(f"{req}: listed in matrix, not tagged in code -> {test}")
    assert not problems, "\n" + "\n".join(problems)


@pytest.mark.requirement("REQ-14")
def test_every_mandatory_requirement_has_a_test():
    uncovered = _mandatory_requirements() - set(_tagged_tests())
    assert uncovered == KNOWN_UNCOVERED, (
        f"uncovered mandatory requirements: {sorted(uncovered)}, "
        f"expected (known gaps): {sorted(KNOWN_UNCOVERED)}"
    )
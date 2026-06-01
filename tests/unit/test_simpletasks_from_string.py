from pathlib import Path
from unittest.mock import patch

import pytest

from opi.input.simple_keywords import SimpleKeyword
from opi.simple_tasks import FreqResults, FreqTask
from opi.simple_tasks import SinglePointResults, SinglePointTask

"""
Unit tests for SimpleTask.from_string classmethod:
- Returns correct _results_type for each task subclass
- Keyword string parsing: splits on spaces, strips leading ! characters
- Working directory handling: non-strict creates/recreates, strict validates
- Optional parameters: ncores, memory, moinp forwarded to input
- Structure is assigned to Calculator
"""

_PATCH_CHECK_VERSION = "opi.core.Calculator.check_version"
_PATCH_WRITE_AND_RUN = "opi.core.Calculator.write_and_run"


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_returns_single_point_results(tmp_path: Path) -> None:
    """SinglePointTask.from_string returns a SinglePointResults instance."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP def2-SVP SP",
            basename="test",
            working_dir=tmp_path / "RUN",
        )
    assert isinstance(result, SinglePointResults)


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_returns_freq_results(tmp_path: Path) -> None:
    """FreqTask.from_string returns a FreqResults instance."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = FreqTask.from_string(
            "B3LYP def2-SVP FREQ",
            basename="test",
            working_dir=tmp_path / "RUN",
        )
    assert isinstance(result, FreqResults)


# ---------------------------------------------------------------------------
# Keyword parsing
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_keywords_without_exclamation(tmp_path: Path) -> None:
    """Keywords without ! are parsed and added to the input correctly."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP def2-SVP",
            basename="test",
            working_dir=tmp_path / "RUN",
        )
    inp = result.calc_object.input
    assert inp.has_simple_keywords(SimpleKeyword("B3LYP"), SimpleKeyword("def2-SVP")) == (
        True,
        True,
    )


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_strips_exclamation_prefix(tmp_path: Path) -> None:
    """Leading ! attached directly to a keyword is stripped before adding it."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "!B3LYP !def2-SVP",
            basename="test",
            working_dir=tmp_path / "RUN",
        )
    inp = result.calc_object.input
    assert inp.has_simple_keywords(SimpleKeyword("B3LYP"), SimpleKeyword("def2-SVP")) == (
        True,
        True,
    )


# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_creates_working_dir(tmp_path: Path) -> None:
    """Non-strict mode creates the working directory when it does not exist."""
    run_dir = tmp_path / "RUN"
    assert not run_dir.exists()
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        SinglePointTask.from_string("B3LYP", basename="test", working_dir=run_dir)
    assert run_dir.exists()


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_strict_raises_if_dir_missing(tmp_path: Path) -> None:
    """strict=True raises ValueError when the working directory does not exist."""
    run_dir = tmp_path / "NONEXISTENT"
    with pytest.raises(ValueError, match="does not exist"):
        SinglePointTask.from_string("B3LYP", basename="test", working_dir=run_dir, strict=True)


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_strict_raises_if_dir_not_empty(tmp_path: Path) -> None:
    """strict=True raises ValueError when the working directory is not empty."""
    run_dir = tmp_path / "RUN"
    run_dir.mkdir()
    (run_dir / "existing.txt").write_text("data")
    with pytest.raises(ValueError, match="not empty"):
        SinglePointTask.from_string("B3LYP", basename="test", working_dir=run_dir, strict=True)


# ---------------------------------------------------------------------------
# Optional parameters
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_sets_ncores(tmp_path: Path) -> None:
    """ncores argument is forwarded to the Calculator input."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP", basename="test", working_dir=tmp_path / "RUN", ncores=4
        )
    assert result.calc_object.input.ncores == 4


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_sets_memory(tmp_path: Path) -> None:
    """memory argument is forwarded to the Calculator input."""
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP", basename="test", working_dir=tmp_path / "RUN", memory=2000
        )
    assert result.calc_object.input.memory == 2000


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_sets_moinp(tmp_path: Path) -> None:
    """moinp argument is forwarded to the Calculator input."""
    mo_file = tmp_path / "prev.gbw"
    mo_file.write_text("")
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP",
            basename="test",
            working_dir=tmp_path / "RUN",
            moinp=mo_file,
        )
    assert result.calc_object.input.moinp == mo_file


@pytest.mark.unit
@pytest.mark.simpletasks
def test_from_string_assigns_structure(tmp_path: Path) -> None:
    """The structure argument is assigned to the Calculator."""
    from opi.input.structures import Structure

    h2 = Structure.from_lists(
        symbols=["H", "H"],
        coordinates=[(0.0, 0.0, 0.0), (0.0, 0.0, 0.74)],
    )
    with patch(_PATCH_CHECK_VERSION), patch(_PATCH_WRITE_AND_RUN, return_value=True):
        result = SinglePointTask.from_string(
            "B3LYP def2-SVP",
            basename="test",
            working_dir=tmp_path / "RUN",
            structure=h2,
        )
    assert result.calc_object.structure is h2

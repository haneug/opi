"""Smoke tests for the SimpleTasks feature.

These tests instantiate each task type and call ``get_input()`` to verify that
the :class:`~opi.input.core.Input` is assembled correctly — no ORCA execution
takes place.
"""

import warnings

import pytest

from opi.input.simple_keywords.task import Task as OrcaTask
from opi.input.structures import Structure
from opi.simple_tasks import EnGradTask, OptTask, SinglePointTask

XYZ_WATER = """3

O         -3.56626        1.77639        0.00000
H         -2.59626        1.77639        0.00000
H         -3.88959        1.36040       -0.81444"""


@pytest.fixture
def water() -> Structure:
    """Minimal water structure for testing."""
    return Structure.from_xyz_block(XYZ_WATER)


# ---------------------------------------------------------------------------
# SinglePointTask
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_single_point_task_keywords_dft():
    """get_input() includes method, basis set, and 'sp' for a DFT task."""
    task = SinglePointTask(method="BP86", basis_set="def2-SVP")
    inp = task.get_input()

    assert inp.has_simple_keywords(OrcaTask.SP)
    assert inp.has_simple_keywords(task.method)
    assert inp.has_simple_keywords(task.basis_set)


@pytest.mark.unit
def test_single_point_task_keywords_sqm():
    """get_input() includes method and 'sp' but no basis set for an SQM task."""
    task = SinglePointTask(method="GFN2-xTB")
    inp = task.get_input()

    assert inp.has_simple_keywords(OrcaTask.SP)
    assert inp.has_simple_keywords(task.method)
    assert task.basis_set is None


@pytest.mark.unit
def test_single_point_task_unknown_method_warns():
    """An unrecognised method string emits a UserWarning and is passed verbatim."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        task = SinglePointTask(method="NOTAMETHOD", basis_set="def2-SVP")

    assert any(issubclass(w.category, UserWarning) for w in caught)
    inp = task.get_input()
    assert inp.has_simple_keywords(OrcaTask.SP)


# ---------------------------------------------------------------------------
# OptTask
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_opt_task_keywords_dft():
    """get_input() includes method, basis set, and 'opt' for a DFT task."""
    task = OptTask(method="r2SCAN", basis_set="def2-TZVP")
    inp = task.get_input()

    assert inp.has_simple_keywords(OrcaTask.OPT)
    assert inp.has_simple_keywords(task.method)
    assert inp.has_simple_keywords(task.basis_set)


@pytest.mark.unit
def test_opt_task_keywords_sqm():
    """get_input() includes method and 'opt' but no basis set for an SQM task."""
    task = OptTask(method="GFN2-xTB")
    inp = task.get_input()

    assert inp.has_simple_keywords(OrcaTask.OPT)
    assert inp.has_simple_keywords(task.method)
    assert task.basis_set is None


# ---------------------------------------------------------------------------
# EnGradTask
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_engrad_task_keywords_dft():
    """get_input() includes method, basis set, and 'engrad' for a DFT task."""
    task = EnGradTask(method="PBE0", basis_set="def2-SVP")
    inp = task.get_input()

    assert inp.has_simple_keywords(OrcaTask.ENGRAD)
    assert inp.has_simple_keywords(task.method)
    assert inp.has_simple_keywords(task.basis_set)


# ---------------------------------------------------------------------------
# JIT construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_input_returns_fresh_object_each_call():
    """get_input() must build a new Input on every call (JIT contract)."""
    task = SinglePointTask(method="HF", basis_set="STO-3G")
    inp1 = task.get_input()
    inp2 = task.get_input()
    assert inp1 is not inp2


# ---------------------------------------------------------------------------
# Mutation safety
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_method_mutation_reflected_in_get_input():
    """Mutating task.method before get_input() is reflected in the new Input."""
    from opi.input.simple_keywords.base import SimpleKeyword

    task = SinglePointTask(method="HF", basis_set="STO-3G")
    task.method = SimpleKeyword("PBE0")
    inp = task.get_input()

    assert inp.has_simple_keywords(SimpleKeyword("PBE0"))

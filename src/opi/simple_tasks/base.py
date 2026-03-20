"""
Base classes for the SimpleTasks feature.

This module provides the abstract base classes :class:`Task` and
:class:`TaskCompleted`, which are the foundation of the high-level task
interface in :mod:`opi.simple_tasks`.
"""

from __future__ import annotations

import typing
import warnings
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from opi.core import Calculator
from opi.input.blocks import Block
from opi.input.core import Input
from opi.input.simple_keywords.basis_set import BasisSet
from opi.input.simple_keywords.base import SimpleKeyword
from opi.input.simple_keywords.method import Method
from opi.input.structures.structure import Structure
from opi.output.core import Output

__all__ = ("Task", "TaskCompleted", "TaskParams")


# ---------------------------------------------------------------------------
# TaskParams
# ---------------------------------------------------------------------------


class TaskParams(BaseModel):
    """Base class for method-family parameter objects.

    Concrete subclasses (``DftParams``, ``SqmParams``, ``WftParams``, …) store
    method-family-specific settings as ``Annotated`` Pydantic fields and use
    this class's machinery to apply them to an :class:`~opi.input.core.Input`.

    The ``Annotated`` metadata controls how each field is mapped:

    * ``Annotated[T, KeywordRegistry]`` — the value is added as a simple
      keyword via :meth:`~opi.input.core.Input.add_simple_keywords`.
    * ``Annotated[T, KeywordRegistry, block_attr_name]`` — the value is
      applied as an attribute inside the corresponding ``%block``.

    Notes
    -----
    The :meth:`validate` model validator resolves raw strings to typed objects
    at construction time, so subclasses receive normalised values immediately.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def map_to_input(self, input_object: Input) -> Input:
        """Apply all parameters to *input_object* and return it.

        Parameters
        ----------
        input_object : Input
            The input object to modify in-place.

        Returns
        -------
        Input
            The same object, with all parameters applied.
        """
        hints = typing.get_type_hints(self.__class__, include_extras=True)

        for field_name, field_type in hints.items():
            value = getattr(self, field_name)
            metadata = typing.get_args(field_type)[1:]

            match metadata:
                case (validator,):
                    input_object.add_simple_keywords(value)
                case (validator, key):
                    block_type = Block.get_subclass_by_name(validator)
                    block_class = block_type(**{key: value})

                    block_exists, *_ = input_object.has_blocks(block_type)
                    if not block_exists:
                        input_object.add_blocks(block_class)
                    else:
                        existing = next(
                            iter(input_object.get_blocks(type(block_class)).values())
                        )
                        merged = block_type.model_validate(
                            {**existing.model_dump(), **block_class.model_dump(exclude_unset=True)}
                        )
                        input_object.add_blocks(merged, overwrite=True)

        return input_object

    @model_validator(mode="before")
    @classmethod
    def validate(cls, data: dict) -> dict:  # type: ignore[override]
        """Resolve raw strings to keyword / block-attribute objects.

        Parameters
        ----------
        data : dict
            Raw field data supplied to the constructor.

        Returns
        -------
        dict
            Data with string values converted to their typed counterparts.
        """
        hints = typing.get_type_hints(cls, include_extras=True)

        for field_name, hint in hints.items():
            if field_name not in data:
                continue

            metadata = typing.get_args(hint)[1:]

            match metadata:
                case (validator,):
                    data[field_name] = validator.find_keyword(data[field_name])
                case (validator, key):
                    block_cls = Block.get_subclass_by_name(validator)
                    instance = block_cls.model_validate({key: data[field_name]})
                    data[field_name] = getattr(instance, key)

        return data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_method(method: str | SimpleKeyword) -> SimpleKeyword:
    """Normalise *method* to a :class:`~opi.input.simple_keywords.base.SimpleKeyword`.

    Parameters
    ----------
    method : str | SimpleKeyword
        Method string or keyword object.

    Returns
    -------
    SimpleKeyword
        Resolved keyword.  If the string is not found in the OPI keyword
        registry a :class:`UserWarning` is emitted and the string is wrapped
        verbatim so the value is still forwarded to ORCA.
    """
    if isinstance(method, SimpleKeyword):
        return method
    try:
        return Method.find_keyword(method)
    except ValueError:
        warnings.warn(
            f"Method {method!r} is not in the OPI keyword registry. "
            "It will be passed to ORCA verbatim.",
            stacklevel=3,
        )
        return SimpleKeyword(method)


def _resolve_basis_set(basis_set: str | SimpleKeyword | None) -> SimpleKeyword | None:
    """Normalise *basis_set* to a :class:`~opi.input.simple_keywords.base.SimpleKeyword`
    or ``None``.

    Parameters
    ----------
    basis_set : str | SimpleKeyword | None
        Basis set string, keyword object, or ``None``.

    Returns
    -------
    SimpleKeyword | None
        Resolved keyword or ``None``.  If the string is not found in the OPI
        keyword registry a :class:`UserWarning` is emitted and the string is
        wrapped verbatim.
    """
    if basis_set is None or isinstance(basis_set, SimpleKeyword):
        return basis_set
    try:
        return BasisSet.find_keyword(basis_set)
    except ValueError:
        warnings.warn(
            f"Basis set {basis_set!r} is not in the OPI keyword registry. "
            "It will be passed to ORCA verbatim.",
            stacklevel=3,
        )
        return SimpleKeyword(basis_set)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class Task(ABC):
    """Abstract base class for high-level ORCA calculation tasks.

    :class:`Task` is a *factory*: it is stateless with respect to individual
    runs.  Each call to :meth:`run` produces an independent
    :class:`TaskCompleted` object and writes no state back to *self*.

    Parameters
    ----------
    method : str | SimpleKeyword
        The computational method (e.g. ``"b3lyp"`` or ``Method.B3LYP``).
        If the string is not found in the OPI keyword registry a
        :class:`UserWarning` is emitted and the value is forwarded to ORCA
        verbatim.
    basis_set : str | SimpleKeyword | None, optional
        The orbital basis set.  May be ``None`` for methods that carry an
        implicit basis set (semi-empirical methods, composite 3c methods, …).
        If the string is not found in the OPI keyword registry a
        :class:`UserWarning` is emitted and the value is forwarded to ORCA
        verbatim.

    Attributes
    ----------
    method : SimpleKeyword
        The normalised method keyword.
    basis_set : SimpleKeyword | None
        The normalised basis-set keyword, or ``None``.

    Notes
    -----
    Input construction is *just-in-time*: the :class:`~opi.input.core.Input`
    object is only assembled when :meth:`get_input` is called, not at
    construction time.
    """

    def __init__(
        self,
        method: str | SimpleKeyword,
        basis_set: str | SimpleKeyword | None = None,
    ) -> None:
        self.method: SimpleKeyword = _resolve_method(method)
        self.basis_set: SimpleKeyword | None = _resolve_basis_set(basis_set)

    # ------------------------------------------------------------------
    # Input / Calculator construction
    # ------------------------------------------------------------------

    def _get_method_params(self) -> "TaskParams | None":
        """Return the method-family parameter object, or ``None``.

        The import is deferred so that :mod:`opi.simple_tasks.method_params`
        is an optional dependency during incremental development.

        Returns
        -------
        TaskParams | None
            A :class:`TaskParams` subclass instance appropriate for the method
            family (DFT, SQM, WFT, …), or ``None`` if the module is not yet
            available.
        """
        try:
            from opi.simple_tasks.method_params import (  # noqa: PLC0415
                get_params_for_method,
            )

            return get_params_for_method(self.method)
        except ImportError:
            return None

    def get_input(self) -> Input:
        """Assemble and return the :class:`~opi.input.core.Input` for this task.

        The :class:`~opi.input.core.Input` is constructed fresh on every call.

        Returns
        -------
        Input
            Fully assembled input object containing at minimum the method
            keyword and, if set, the basis-set keyword.
        """
        inp = Input()
        inp.add_simple_keywords(self.method)
        if self.basis_set is not None:
            inp.add_simple_keywords(self.basis_set)
        params = self._get_method_params()
        if params is not None:
            inp = params.map_to_input(inp)
        return inp

    def get_calculator(
        self,
        basename: str,
        structure: Structure,
        working_dir: Path,
    ) -> Calculator:
        """Return a fully configured :class:`~opi.core.Calculator`.

        Parameters
        ----------
        basename : str
            Basename for all files written by the ORCA process.
        structure : Structure
            Molecular structure.
        working_dir : Path
            Directory in which the calculation will be executed.
            Must already exist before this method is called.

        Returns
        -------
        Calculator
        """
        calc = Calculator(basename, working_dir=working_dir, version_check=False)
        calc.structure = structure
        calc.input = self.get_input()
        return calc

    # ------------------------------------------------------------------
    # Running
    # ------------------------------------------------------------------

    @staticmethod
    def _job_is_completed(basename: str, working_dir: Path) -> bool:
        """Return ``True`` when a successfully completed job is found.

        A job is considered complete when the ``<basename>.property.json``
        file exists *and* the ORCA output file contains the normal-termination
        marker.

        Parameters
        ----------
        basename : str
        working_dir : Path
        """
        property_json = working_dir / f"{basename}.property.json"
        if not property_json.exists():
            return False
        out = Output(basename=basename, working_dir=working_dir, version_check=False)
        return out.terminated_normally()

    def run(
        self,
        basename: str,
        structure: Structure,
        working_dir: Path | None = None,
        ncores: int | None = None,
        memory_per_core: int | None = None,
        force: bool = False,
        reuse_completed: bool = False,
    ) -> "TaskCompleted":
        """Execute the ORCA calculation.

        Parameters
        ----------
        basename : str
            Basename for all files created by ORCA.
        structure : Structure
            Molecular structure.
        working_dir : Path | None, optional
            Directory in which the calculation is executed.  If ``None``, a
            subdirectory named *basename* inside the current working directory
            is used.
        ncores : int | None, optional
            Number of CPU cores passed to ORCA via the ``%pal`` block.
        memory_per_core : int | None, optional
            Memory per core in MB, passed to ORCA via the ``%maxcore``
            directive.
        force : bool, default: False
            If ``True`` and *working_dir* already exists, overwrite its
            contents without raising an error.
        reuse_completed : bool, default: False
            If ``True`` and *working_dir* contains a successfully completed
            job, skip execution and reconstruct the result from disk.

        Returns
        -------
        TaskCompleted
            Result object for the completed job.

        Raises
        ------
        RuntimeError
            * If *working_dir* already exists and neither *force* nor
              *reuse_completed* is set.
            * If *reuse_completed* is ``True`` but the existing job did not
              complete successfully.
        """
        if working_dir is None:
            working_dir = Path(basename)
        working_dir = working_dir.expanduser().resolve()

        if working_dir.exists():
            if reuse_completed:
                if not self._job_is_completed(basename, working_dir):
                    raise RuntimeError(
                        f"reuse_completed=True but the job in {working_dir} did not "
                        "complete successfully. Remove the directory or re-run with "
                        "force=True."
                    )
                calc = Calculator(basename, working_dir=working_dir, version_check=False)
                return self._make_completed(calc)
            elif not force:
                raise RuntimeError(
                    f"Working directory {working_dir} already exists. "
                    "Pass force=True to overwrite or reuse_completed=True to reuse a "
                    "previously completed job."
                )
            # force=True and directory exists: fall through, overwrite files below
        else:
            working_dir.mkdir(parents=True)

        calc = self.get_calculator(basename, structure, working_dir)

        if ncores is not None:
            calc.input.ncores = ncores
        if memory_per_core is not None:
            calc.input.memory = memory_per_core

        calc.write_and_run(force=True)
        return self._make_completed(calc)

    @abstractmethod
    def _make_completed(self, calculator: Calculator) -> "TaskCompleted":
        """Construct the concrete :class:`TaskCompleted` subclass.

        Called internally by :meth:`run` after the job finishes (or when
        reconstructing a result from disk via *reuse_completed*).

        Parameters
        ----------
        calculator : Calculator
            The calculator used for this job.

        Returns
        -------
        TaskCompleted
        """
        ...


# ---------------------------------------------------------------------------
# TaskCompleted
# ---------------------------------------------------------------------------


class TaskCompleted(ABC):
    """Abstract base class for task results.

    Parameters
    ----------
    calculator : Calculator
        The calculator that was used to execute the job.  Retained so that the
        job can be inspected or restarted.

    Attributes
    ----------
    calculator : Calculator
        See *calculator* parameter.
    """

    def __init__(self, calculator: Calculator) -> None:
        self.calculator: Calculator = calculator

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def status(self) -> bool:
        """Whether the job terminated normally.

        Subclasses may override this property to add task-specific convergence
        checks (e.g. SCF convergence for single-point jobs, geometry
        convergence for optimisations).

        Returns
        -------
        bool
        """
        return self.get_output().terminated_normally()

    # ------------------------------------------------------------------
    # Primary result
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def primary_property(self):
        """The main chemical result of the task.

        The concrete type and semantics are defined by each subclass.
        See :class:`~opi.simple_tasks.results.SinglePointCompleted`,
        :class:`~opi.simple_tasks.results.OptCompleted`, and
        :class:`~opi.simple_tasks.results.EnGradCompleted`.
        """
        ...

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_output(self) -> Output:
        """Return an :class:`~opi.output.core.Output` for this job.

        This is the primary escape hatch to the full ORCA output.

        Returns
        -------
        Output
        """
        return self.calculator.get_output()

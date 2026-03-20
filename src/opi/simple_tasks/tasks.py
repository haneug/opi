"""Concrete task classes for the SimpleTasks feature.

Each class wraps a specific ORCA calculation type and narrows the return type
of :meth:`~opi.simple_tasks.base.Task.run` to the appropriate
:class:`~opi.simple_tasks.base.TaskCompleted` subclass.

The execution logic lives entirely on the base :class:`~opi.simple_tasks.base.Task`
class; the subclasses here only add the ORCA task keyword to the
:class:`~opi.input.core.Input` and instantiate the correct result object.
"""

from __future__ import annotations

from typing import cast

from opi.core import Calculator
from opi.input.core import Input
from opi.input.simple_keywords.task import Task as OrcaTask
from opi.input.structures.structure import Structure
from opi.simple_tasks.base import Task
from opi.simple_tasks.results import EnGradCompleted, OptCompleted, SinglePointCompleted

__all__ = ("EnGradTask", "OptTask", "SinglePointTask")


class SinglePointTask(Task):
    """High-level single-point energy calculation.

    Runs an ORCA single-point calculation (``! sp``) and returns a
    :class:`~opi.simple_tasks.results.SinglePointCompleted` whose
    :attr:`~opi.simple_tasks.results.SinglePointCompleted.primary_property`
    is the final total electronic energy in Hartree.

    Parameters
    ----------
    method : str | SimpleKeyword
        The computational method (e.g. ``"BP86"``, ``"B3LYP"``).
    basis_set : str | SimpleKeyword | None, optional
        The orbital basis set.  May be ``None`` for semi-empirical methods.

    Examples
    --------
    >>> sp = SinglePointTask(method="BP86", basis_set="SV(P)")
    >>> result = sp.run(basename="water_sp", structure=structure,
    ...                 working_dir=Path("water_sp"))
    >>> energy = result.primary_property  # float, Hartree
    """

    def get_input(self) -> Input:
        """Assemble the Input, including the ``sp`` task keyword.

        Returns
        -------
        Input
        """
        inp = super().get_input()
        inp.add_simple_keywords(OrcaTask.SP)
        return inp

    def _make_completed(self, calculator: Calculator) -> SinglePointCompleted:
        """Construct a :class:`~opi.simple_tasks.results.SinglePointCompleted`.

        Parameters
        ----------
        calculator : Calculator

        Returns
        -------
        SinglePointCompleted
        """
        return SinglePointCompleted(calculator)

    def run(  # type: ignore[override]
        self,
        basename: str,
        structure: Structure,
        working_dir=None,
        ncores: int | None = None,
        memory_per_core: int | None = None,
        force: bool = False,
        reuse_completed: bool = False,
    ) -> SinglePointCompleted:
        """Execute the single-point calculation.

        Parameters
        ----------
        basename : str
            Basename for all files created by ORCA.
        structure : Structure
            Molecular structure.
        working_dir : Path | None, optional
            Directory in which the calculation is executed.
        ncores : int | None, optional
            Number of CPU cores.
        memory_per_core : int | None, optional
            Memory per core in MB.
        force : bool, default: False
            Overwrite an existing working directory.
        reuse_completed : bool, default: False
            Return a result built from an existing successful run.

        Returns
        -------
        SinglePointCompleted
        """
        return cast(
            SinglePointCompleted,
            super().run(
                basename=basename,
                structure=structure,
                working_dir=working_dir,
                ncores=ncores,
                memory_per_core=memory_per_core,
                force=force,
                reuse_completed=reuse_completed,
            ),
        )


class OptTask(Task):
    """High-level geometry optimisation.

    Runs an ORCA geometry optimisation (``! opt``) and returns an
    :class:`~opi.simple_tasks.results.OptCompleted` whose
    :attr:`~opi.simple_tasks.results.OptCompleted.primary_property`
    is a ``(energy, structure)`` tuple containing the final energy in Hartree
    and the optimised geometry as a
    :class:`~opi.input.structures.structure.Structure`.

    Parameters
    ----------
    method : str | SimpleKeyword
        The computational method (e.g. ``"GFN2-xTB"``, ``"r2SCAN"``).
    basis_set : str | SimpleKeyword | None, optional
        The orbital basis set.  May be ``None`` for semi-empirical methods.

    Examples
    --------
    >>> opt = OptTask(method="GFN2-xTB")
    >>> result = opt.run(basename="water_opt", structure=structure,
    ...                  working_dir=Path("water_opt"))
    >>> energy, optimised_structure = result.primary_property
    """

    def get_input(self) -> Input:
        """Assemble the Input, including the ``opt`` task keyword.

        Returns
        -------
        Input
        """
        inp = super().get_input()
        inp.add_simple_keywords(OrcaTask.OPT)
        return inp

    def _make_completed(self, calculator: Calculator) -> OptCompleted:
        """Construct an :class:`~opi.simple_tasks.results.OptCompleted`.

        Parameters
        ----------
        calculator : Calculator

        Returns
        -------
        OptCompleted
        """
        return OptCompleted(calculator)

    def run(  # type: ignore[override]
        self,
        basename: str,
        structure: Structure,
        working_dir=None,
        ncores: int | None = None,
        memory_per_core: int | None = None,
        force: bool = False,
        reuse_completed: bool = False,
    ) -> OptCompleted:
        """Execute the geometry optimisation.

        Parameters
        ----------
        basename : str
            Basename for all files created by ORCA.
        structure : Structure
            Molecular structure.
        working_dir : Path | None, optional
            Directory in which the calculation is executed.
        ncores : int | None, optional
            Number of CPU cores.
        memory_per_core : int | None, optional
            Memory per core in MB.
        force : bool, default: False
            Overwrite an existing working directory.
        reuse_completed : bool, default: False
            Return a result built from an existing successful run.

        Returns
        -------
        OptCompleted
        """
        return cast(
            OptCompleted,
            super().run(
                basename=basename,
                structure=structure,
                working_dir=working_dir,
                ncores=ncores,
                memory_per_core=memory_per_core,
                force=force,
                reuse_completed=reuse_completed,
            ),
        )


class EnGradTask(Task):
    """High-level energy and gradient calculation.

    Runs an ORCA energy+gradient calculation (``! engrad``) and returns an
    :class:`~opi.simple_tasks.results.EnGradCompleted` whose
    :attr:`~opi.simple_tasks.results.EnGradCompleted.primary_property`
    is a ``(energy, gradient)`` tuple.  The gradient is a flat tuple of
    Cartesian components (x, y, z per atom) in Eh/Bohr.

    Parameters
    ----------
    method : str | SimpleKeyword
        The computational method (e.g. ``"BP86"``).
    basis_set : str | SimpleKeyword | None, optional
        The orbital basis set.

    Examples
    --------
    >>> task = EnGradTask(method="BP86", basis_set="def2-SVP")
    >>> result = task.run(basename="water_eg", structure=structure,
    ...                   working_dir=Path("water_eg"))
    >>> energy, gradient = result.primary_property
    """

    def get_input(self) -> Input:
        """Assemble the Input, including the ``engrad`` task keyword.

        Returns
        -------
        Input
        """
        inp = super().get_input()
        inp.add_simple_keywords(OrcaTask.ENGRAD)
        return inp

    def _make_completed(self, calculator: Calculator) -> EnGradCompleted:
        """Construct an :class:`~opi.simple_tasks.results.EnGradCompleted`.

        Parameters
        ----------
        calculator : Calculator

        Returns
        -------
        EnGradCompleted
        """
        return EnGradCompleted(calculator)

    def run(  # type: ignore[override]
        self,
        basename: str,
        structure: Structure,
        working_dir=None,
        ncores: int | None = None,
        memory_per_core: int | None = None,
        force: bool = False,
        reuse_completed: bool = False,
    ) -> EnGradCompleted:
        """Execute the energy and gradient calculation.

        Parameters
        ----------
        basename : str
            Basename for all files created by ORCA.
        structure : Structure
            Molecular structure.
        working_dir : Path | None, optional
            Directory in which the calculation is executed.
        ncores : int | None, optional
            Number of CPU cores.
        memory_per_core : int | None, optional
            Memory per core in MB.
        force : bool, default: False
            Overwrite an existing working directory.
        reuse_completed : bool, default: False
            Return a result built from an existing successful run.

        Returns
        -------
        EnGradCompleted
        """
        return cast(
            EnGradCompleted,
            super().run(
                basename=basename,
                structure=structure,
                working_dir=working_dir,
                ncores=ncores,
                memory_per_core=memory_per_core,
                force=force,
                reuse_completed=reuse_completed,
            ),
        )

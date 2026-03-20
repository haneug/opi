"""
Concrete result classes for the SimpleTasks feature.

Each class wraps a completed ORCA job and exposes a ``primary_property``
that gives direct access to the main chemical result of that task type.
"""

from __future__ import annotations

from opi.input.structures.structure import Structure
from opi.simple_tasks.base import TaskCompleted

__all__ = ("SinglePointCompleted", "OptCompleted", "EnGradCompleted")


class SinglePointCompleted(TaskCompleted):
    """Result of a :class:`~opi.simple_tasks.tasks.SinglePointTask`.

    Attributes
    ----------
    calculator : ~opi.core.Calculator
        The calculator used to run this job.
    """

    @property
    def status(self) -> bool:
        """Whether the job terminated normally *and* the SCF converged.

        Returns
        -------
        bool
        """
        out = self.get_output()
        return out.terminated_normally() and out.scf_converged()

    @property
    def primary_property(self) -> float:
        """Final single-point energy in Hartree.

        Returns
        -------
        float
            Total electronic energy in Hartree.

        Raises
        ------
        RuntimeError
            If the energy cannot be retrieved from the output (e.g. the job
            did not complete successfully).
        """
        energy = self.get_output().get_final_energy()
        if energy is None:
            raise RuntimeError(
                "Could not retrieve the final energy from the ORCA output. "
                "Check that the job completed successfully."
            )
        return float(energy)


class OptCompleted(TaskCompleted):
    """Result of an :class:`~opi.simple_tasks.tasks.OptTask`.

    Attributes
    ----------
    calculator : ~opi.core.Calculator
        The calculator used to run this job.
    """

    @property
    def status(self) -> bool:
        """Whether the job terminated normally *and* the geometry optimisation converged.

        Returns
        -------
        bool
        """
        out = self.get_output()
        return out.terminated_normally() and out.geometry_optimization_converged()

    @property
    def primary_property(self) -> tuple[float, Structure]:
        """Final energy and optimised geometry.

        Returns
        -------
        tuple[float, Structure]
            A two-element tuple ``(energy, structure)`` where *energy* is the
            total electronic energy of the optimised geometry in Hartree and
            *structure* is the optimised geometry as a
            :class:`~opi.input.structures.structure.Structure`.

        Raises
        ------
        RuntimeError
            If either the energy or the structure cannot be retrieved from the
            output (e.g. the job did not complete successfully).
        """
        out = self.get_output()
        energy = out.get_final_energy()
        structure = out.get_structure()

        if energy is None:
            raise RuntimeError(
                "Could not retrieve the final energy from the ORCA output. "
                "Check that the job completed successfully."
            )
        if structure is None:
            raise RuntimeError(
                "Could not retrieve the optimised structure from the ORCA output. "
                "Check that the job completed successfully."
            )
        return float(energy), structure


class EnGradCompleted(TaskCompleted):
    """Result of an :class:`~opi.simple_tasks.tasks.EnGradTask`.

    Attributes
    ----------
    calculator : ~opi.core.Calculator
        The calculator used to run this job.
    """

    @property
    def primary_property(self) -> tuple[float, tuple[float, ...]]:
        """Final energy and nuclear gradient.

        Returns
        -------
        tuple[float, tuple[float, ...]]
            A two-element tuple ``(energy, gradient)`` where *energy* is the
            total electronic energy in Hartree and *gradient* is a flat tuple
            of Cartesian gradient components ordered as x, y, z for atom 1,
            x, y, z for atom 2, … in Eh/Bohr.

        Raises
        ------
        RuntimeError
            If either the energy or the gradient cannot be retrieved from the
            output (e.g. the job did not complete successfully).
        """
        out = self.get_output()
        energy = out.get_final_energy()
        gradient = out.get_gradient()

        if energy is None:
            raise RuntimeError(
                "Could not retrieve the final energy from the ORCA output. "
                "Check that the job completed successfully."
            )
        if gradient is None:
            raise RuntimeError(
                "Could not retrieve the nuclear gradient from the ORCA output. "
                "Check that the job completed successfully."
            )
        return float(energy), tuple(float(g) for g in gradient)

import typing
from functools import cached_property

from opi.input.simple_keywords import SimpleKeyword, Solvent, Task
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class FreqSettings(TaskSettings):
    """Task settings for frequency calculations (``! FREQ``)."""

    _name: str = "freq"
    task_keyword: typing.Annotated[SimpleKeyword, Task] = Task.FREQ


class FreqTask(SimpleTask):
    """
    High-level task for harmonic frequency calculations.

    Returns a ``FreqResults`` object.  ``status`` is ``True`` when the job
    terminated normally (SCF convergence is not checked separately because
    frequency jobs always follow an SCF step).
    """

    _task_settings: FreqSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: FreqSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings_type = FreqSettings
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )

        self._results_type = FreqResults


class FreqResults(TaskResults):
    """Results from a harmonic frequency calculation."""

    @cached_property
    def status(self) -> bool:
        """``True`` if the job terminated normally (SCF convergence not re-checked)."""
        return self.output.terminated_normally()

    @cached_property
    def free_energy_delta(self) -> float:
        """
        Thermal free-energy correction (ΔG) in Hartree.

        Raises
        ------
        ValueError
            If the free-energy correction is not present in the ORCA output.
        """
        free_energy_delta = self.output.get_free_energy_delta()

        if free_energy_delta is None:
            raise ValueError("Could not get free energy delta from ORCA output")

        return free_energy_delta

    @property
    def primary_property(self) -> float:
        """Alias for ``free_energy_delta``."""
        return float(self.free_energy_delta)

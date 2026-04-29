import typing

from opi.input.simple_keywords import SimpleKeyword, Solvent, Task
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class EngradSettings(TaskSettings):
    _name: str = "engrad"
    task_keyword: typing.Annotated[SimpleKeyword, Task] = Task.ENGRAD


class EngradTask(SimpleTask):
    _task_settings: EngradSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: EngradSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings_type = EngradSettings
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )

        self._results_type = EngradResults


class EngradResults(TaskResults):
    @property
    def final_energy(self) -> float:
        final_energy = self.output.get_final_energy()

        if final_energy is None:
            raise ValueError("Could not get final energy from ORCA Output")

        return final_energy

    @property
    def gradient(self) -> list[float]:
        gradient = self.output.get_gradient()

        if gradient is None:
            raise ValueError("Could not get gradient from ORCA Output")

        return gradient

    @property
    def primary_property(self) -> tuple[float, list[float]]:
        return self.final_energy, self.gradient

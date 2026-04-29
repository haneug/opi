import typing
from pathlib import Path

from opi.input.simple_keywords import SimpleKeyword, Solvent, Task
from opi.input.structures import BaseStructureFile, Structure
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class SinglePointSettings(TaskSettings):
    _name: str = "singlepoint"
    task_keyword: typing.Annotated[SimpleKeyword, Task] = Task.SP


class SinglePointTask(SimpleTask):
    _task_settings: SinglePointSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: SinglePointSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings_type = SinglePointSettings
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )

        self._results_type = SinglePointResults

    def run(
        self,
        basename: str,
        struct: Structure | BaseStructureFile,
        working_dir: Path = Path("RUN"),
        ncores: int | None = None,
        memory: int | None = None,
        moinp: Path | None = None,
        strict: bool = False,
    ) -> "SinglePointResults":
        single_point_result = super().run(
            basename=basename,
            struct=struct,
            working_dir=working_dir,
            ncores=ncores,
            memory=memory,
            moinp=moinp,
            strict=strict,
        )

        return typing.cast(SinglePointResults, single_point_result)


class SinglePointResults(TaskResults):
    @property
    def final_energy(self) -> float:
        final_energy = self.output.get_final_energy()

        if final_energy is None:
            raise ValueError("Could not get final energy from ORCA Output")

        return final_energy

    @property
    def primary_property(self) -> float:
        return float(self.final_energy)

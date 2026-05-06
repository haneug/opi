import typing
from functools import cached_property

from opi.input import Input
from opi.input.simple_keywords import Goat, SimpleKeyword, Solvent
from opi.input.structures import Structure, Properties
from opi.simpletasks.base_task import TaskSettings, SimpleTask, TaskResults
from opi.simpletasks.method_settings import MethodSettings


class GoatSettings(TaskSettings):
    _name: str = "goat"
    task_keyword : typing.Annotated[SimpleKeyword, Goat]= Goat.GOAT
    goat_maxiter: typing.Annotated[int, "BlockGoat", "maxiter"] | None = None
    goat_react: bool | None = None
    goat_diversity: bool | None = None
    goat_explore: bool | None = None

    def map_to_input(self, input_object: Input) -> Input:
        super().map_to_input(input_object)

        if self.goat_react:
            input_object.add_simple_keywords(Goat.GOAT_REACT)

        if self.goat_diversity:
            input_object.add_simple_keywords(Goat.GOAT_DIVERSITY)

        if self.goat_explore:
            input_object.add_simple_keywords(Goat.GOAT_EXPLORE)

        return input_object


class GoatTask(SimpleTask):
    _task_settings: GoatSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: GoatSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings_type = GoatSettings
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )

        self._results_type = GoatResults


class GoatResults(TaskResults):
    @cached_property
    def status(self) -> bool:
        return self.output.terminated_normally()

    @cached_property
    def structures(self) -> list[Structure]:
        structures = Structure.from_trj_xyz(self.output.working_dir/ f"{self.output.basename}.finalensemble.xyz")
        return structures

    @cached_property
    def properties(self) -> list[Properties]:
        properties = Properties.from_trj_xyz(self.output.working_dir / f"{self.output.basename}.finalensemble.xyz", mode="goat")
        return properties

    @cached_property
    def primary_property(self) -> tuple[list[Structure], list[Properties]]:
        return self.structures, self.properties





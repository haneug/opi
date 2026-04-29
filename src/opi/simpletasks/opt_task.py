import typing
from pathlib import Path

from opi.input import Input
from opi.input.simple_keywords import SimpleKeyword, Solvent, Task
from opi.input.simple_keywords.opt import Opt, OptThreshold
from opi.input.structures import BaseStructureFile, Structure
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class OptSettings(TaskSettings):
    _name: str = "opt"
    task_keyword: typing.Annotated[SimpleKeyword, Task] = Task.OPT
    opt_threshold: typing.Annotated[SimpleKeyword, OptThreshold] | None = None
    optrigid: bool = False
    opt_h: bool = False
    lopt: bool = False
    opt_maxiter: typing.Annotated[int, "BlockGeom", "maxiter"] | None = None

    def map_to_input(self, input_object: Input) -> Input:
        input_object = super().map_to_input(input_object)

        if self.optrigid:
            input_object.add_simple_keywords(Opt.RIGIDBODYOPT)

        opt_map = {
            (True, True): Opt.L_OPTH,
            (True, False): Opt.OPTH,
            (False, True): Opt.L_OPT,
        }

        keyword = opt_map.get((self.opt_h, self.lopt))
        if keyword:
            input_object.add_simple_keywords(keyword)

        return input_object


class OptTask(SimpleTask):
    _task_settings: OptSettings

    def __init__(
        self,
        method: str | SimpleKeyword,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: OptSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings_type = OptSettings
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )

        self._results_type = OptResults

    def run(
        self,
        basename: str,
        struct: Structure | BaseStructureFile,
        working_dir: Path = Path("RUN"),
        ncores: int | None = None,
        memory: int | None = None,
        moinp: Path | None = None,
        strict: bool = False,
    ) -> "OptResults":
        single_point_result = super().run(
            basename=basename,
            struct=struct,
            working_dir=working_dir,
            ncores=ncores,
            memory=memory,
            moinp=moinp,
            strict=strict,
        )

        return typing.cast(OptResults, single_point_result)

    @property
    def opt_threshold(self) -> SimpleKeyword | None:
        return self._task_settings.opt_threshold

    @opt_threshold.setter
    def opt_threshold(self, new_value: SimpleKeyword | str) -> None:
        self._task_settings.opt_threshold = new_value  # type:ignore

    @property
    def optrigid(self) -> bool:
        return self._task_settings.optrigid

    @optrigid.setter
    def optrigid(self, new_value: bool) -> None:
        self._task_settings.optrigid = new_value

    @property
    def opt_h(self) -> bool:
        return self._task_settings.opt_h

    @opt_h.setter
    def opt_h(self, new_value: bool) -> None:
        self._task_settings.opt_h = new_value

    @property
    def lopt(self) -> bool:
        return self._task_settings.lopt

    @lopt.setter
    def lopt(self, new_value: bool) -> None:
        self._task_settings.lopt = new_value

    @property
    def opt_maxiter(self) -> int | None:
        return self._task_settings.opt_maxiter

    @opt_maxiter.setter
    def opt_maxiter(self, new_value: int | None) -> None:
        self._task_settings.opt_maxiter = new_value


class OptResults(TaskResults):
    @property
    @TaskResults.output_parse
    def final_energy(self) -> float:
        final_energy = self.output.get_final_energy()

        if final_energy is None:
            raise ValueError("Could not get final energy from ORCA Output")

        return final_energy

    @property
    @TaskResults.output_parse
    def structure(self) -> Structure:
        structure = self.output.get_structure()
        if structure is None:
            raise ValueError("Could not get structure from ORCA Output")

        return structure

    @property
    def primary_property(self) -> tuple[float, Structure]:
        return self.final_energy, self.structure

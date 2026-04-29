import shutil
import typing
import warnings
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path

from pydantic import ConfigDict

from opi.core import Calculator
from opi.input import Input
from opi.input.simple_keywords import (
    SimpleKeyword,
    SimpleKeywordBox,
    Solvent,
)
from opi.input.structures import BaseStructureFile, Structure
from opi.output.core import Output
from opi.simpletasks.method_settings import MethodSettings
from opi.simpletasks.settings import Settings


class TaskSettings(Settings):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra="forbid")
    task_keyword: typing.Annotated[SimpleKeyword, SimpleKeywordBox]


class SimpleTask(ABC):
    _results_type: type["TaskResults"]
    _task_settings_type: type[TaskSettings]
    _task_settings: TaskSettings
    _method_settings: MethodSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: "TaskSettings | dict[str, typing.Any] | None" = None,
        method_settings: "MethodSettings | dict[str, typing.Any] | None" = None,
    ):
        if isinstance(task_settings, dict):
            self._task_settings = self._task_settings_type.model_validate(task_settings)
        else:
            self._task_settings = task_settings or self._task_settings_type()  # type: ignore[call-arg]

        resolved_method_settings: MethodSettings | None = (
            MethodSettings(**method_settings)
            if isinstance(method_settings, dict)
            else method_settings
        )

        if method is not None:
            resolved_type = MethodSettings.resolve_method_settings_type(method)
            base_data: dict[str, typing.Any] = {
                k: v
                for k, v in {
                    "method": method,
                    "basis_set": basis_set,
                    "solvation_model": solvation_model,
                    "solvent": solvent,
                }.items()
                if v is not None
            }
            if resolved_method_settings is not None:
                extra: dict[str, typing.Any] = {
                    **resolved_method_settings.model_dump(exclude_unset=True),
                    **(resolved_method_settings.model_extra or {}),
                }
                self._method_settings = resolved_type(**{**extra, **base_data})
            else:
                self._method_settings = resolved_type(**base_data)
        else:
            if resolved_method_settings is None:
                raise ValueError(
                    "Either 'method' or a 'method_settings' object with a method must be provided"
                )
            self._method_settings = resolved_method_settings

    @property
    def task_settings(self) -> TaskSettings:
        return self._task_settings

    @property
    def method_settings(self) -> MethodSettings:
        return self._method_settings

    @property
    def input_object(self) -> Input:
        """
        Creates configured `Input` object. First it initializes an empty instance of `Input` , and then passes it as
        to corresponding `TaskSettings` and `MethodSettings` objects to be configured by user-defined data stored in those
        objects.

        Returns
        -------
        `Input`
            `Input` object configured by user-defined data.

        """
        inp = Input()
        inp = self._task_settings.map_to_input(input_object=inp)
        inp = self.method_settings.map_to_input(input_object=inp)
        return inp

    @property
    def keyword(self) -> SimpleKeyword:
        return self._task_settings.task_keyword

    @property
    def method(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "method"):
            return self._method_settings.method
        return None

    @method.setter
    def method(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "method"):
            raise AttributeError("method is not defined in method_settings object")
        if new_value is None:
            self._method_settings.method = None  # type:ignore
            return
        resolved_type = MethodSettings.resolve_method_settings_type(new_value)
        if isinstance(self._method_settings, resolved_type):
            self._method_settings.method = new_value  # type:ignore
        else:
            common_fields: dict[str, typing.Any] = {"method": new_value}
            for field in ("basis_set", "solvation_model", "solvent"):
                if field in resolved_type.model_fields:
                    val = getattr(self._method_settings, field, None)
                    if val is not None:
                        common_fields[field] = val
            dropped = [
                f
                for f, v in self._method_settings.model_dump(exclude_unset=True).items()
                if f not in common_fields and v is not None
            ]
            if dropped:
                warnings.warn(
                    f"Switching method family dropped settings: {', '.join(dropped)}",
                    UserWarning,
                    stacklevel=2,
                )
            self._method_settings = resolved_type(**common_fields)

    @property
    def basis_set(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "basis_set"):
            return self._method_settings.basis_set
        return None

    @basis_set.setter
    def basis_set(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "basis_set"):
            raise AttributeError("basis_set is not defined in method_settings object")
        self._method_settings.basis_set = new_value  # type:ignore

    @property
    def solvent(self) -> str | None:
        if hasattr(self._method_settings, "solvent"):
            return self._method_settings.solvent
        return None

    @solvent.setter
    def solvent(self, new_value: str | None) -> None:
        if not hasattr(self._method_settings, "solvent"):
            raise AttributeError("solvent is not defined in method_settings object")
        self._method_settings.solvent = new_value

    @property
    def solvation_model(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "solvation_model"):
            return self._method_settings.solvation_model
        return None

    @solvation_model.setter
    def solvation_model(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "solvation_model"):
            raise AttributeError("solvation_model is not defined in method_settings object")
        self._method_settings.solvation_model = new_value  # type:ignore

    def run(
        self,
        basename: str,
        struct: Structure | BaseStructureFile,
        working_dir: Path = Path("RUN"),
        ncores: int | None = None,
        memory: int | None = None,
        moinp: Path | None = None,
        strict: bool = False,
    ) -> "TaskResults":
        """
        Execute the computational task with the given structure and settings.

        This method prepares the working directory, configures the calculation
        input parameters, and runs the calculation using an external calculator.
        The results are returned as an instance of the configured results type.

        Parameters
        ----------
        basename : str
            Base name for the calculation.
        struct : Structure or BaseStructureFile
            The input structure for the calculation.
        working_dir : pathlib.Path, optional
            Directory in which the calculation will be executed.
            If it exists, it will be removed and recreated. Defaults to "RUN".
        ncores : int, optional
            Number of CPU cores to use for the calculation. Overrides the default
            value in the input object if provided.
        memory : int, optional
            Amount of memory to allocate for the calculation. Overrides the default
            value in the input object if provided.
        moinp : pathlib.Path, optional
            Path to a molecular orbital input file. Overrides the default if provided.
        strict : bool, optional
            Controls whether working directory will be created/overwritten. Defaults to False.

        Returns
        -------
        TaskResults
            An instance of the configured results type containing the results
            of the calculation.
        """
        if strict:
            # Must already exist
            if not working_dir.exists():
                raise ValueError(
                    f"Working directory {working_dir.resolve()} does not exist (strict mode)"
                )

            # Must be empty
            if any(working_dir.iterdir()):
                raise ValueError(
                    f"Working directory {working_dir.resolve()} is not empty (strict mode)"
                )

        else:
            # Non-strict: recreate directory
            if working_dir.exists():
                shutil.rmtree(working_dir)
            working_dir.mkdir()

        inp = self.input_object

        if ncores is not None:
            inp.ncores = ncores

        if memory is not None:
            inp.memory = memory

        if moinp is not None:
            inp.moinp = moinp

        calc = Calculator(basename, working_dir=working_dir)
        calc.structure = struct
        calc.input = inp

        calc.write_and_run()

        return self._results_type(calc_object=calc)

    def _restart(
        self,
        previous_results: "TaskResults",
        basename: str | None = None,
        struct: Structure | BaseStructureFile | None = None,
        working_dir: Path | None = None,
        ncores: int | None = None,
        memory: int | None = None,
        moinp: Path | None = None,
        use_previous_orbitals: bool = False,
    ) -> "TaskResults":
        """
        TODO:
        - finish restart implementation (low on priority list)
        Parameters
        ----------
        previous_results
        basename
        struct
        working_dir
        ncores
        memory
        moinp
        use_previous_orbitals

        Returns
        -------

        """
        prev_calc = previous_results.calc_object

        basename = basename if basename else prev_calc.basename
        struct = struct if struct else prev_calc.structure
        if struct is None:
            raise ValueError(
                "No structure available for restart: previous calculation had no structure set"
            )
        working_dir = working_dir if working_dir else prev_calc.working_dir
        ncores = ncores if ncores else prev_calc.input.ncores
        memory = memory if memory else prev_calc.input.memory

        if use_previous_orbitals:
            prev_gbw = prev_calc.working_dir / f"{prev_calc.basename}.gbw"
            if not prev_gbw.exists():
                raise FileNotFoundError(f"GBW file not found: {prev_gbw}")
            moinp = prev_gbw
        else:
            moinp = moinp if moinp else prev_calc.input.moinp

        return self.run(basename, struct, working_dir, ncores, memory, moinp)


class TaskResults(ABC):
    def __init__(self, calc_object: Calculator):
        self.calc_object = calc_object

    @cached_property
    def output(self) -> Output:
        if not self.calc_object:
            raise ValueError("calc_object not set")

        out = self.calc_object.get_output()
        out.parse()
        return out

    @cached_property
    def status(self) -> bool:
        return self.output.terminated_normally() and self.output.scf_converged()

    @cached_property
    @abstractmethod
    def primary_property(self) -> typing.Any:
        pass

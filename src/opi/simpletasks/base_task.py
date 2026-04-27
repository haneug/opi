import shutil
import typing
from abc import ABC, abstractmethod
from functools import cached_property, wraps
from pathlib import Path

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
    task_keyword: typing.Annotated[SimpleKeyword, SimpleKeywordBox]


class SimpleTask(ABC):
    _results_type: type["TaskResults"]
    _task_settings_type: typing.Callable[[], TaskSettings]
    _task_settings: TaskSettings
    _method_settings: MethodSettings

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: TaskSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        self._task_settings = task_settings or self._task_settings_type()

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
            if method_settings is not None:
                extra: dict[str, typing.Any] = {
                    **method_settings.model_dump(exclude_unset=True),
                    **(method_settings.model_extra or {}),
                }
                self._method_settings = resolved_type(**{**extra, **base_data})
            else:
                self._method_settings = resolved_type(**base_data)
        else:
            if method_settings is None:
                raise ValueError(
                    "Either 'method' or a 'method_settings' object with a method must be provided"
                )
            self._method_settings = method_settings

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
        self._method_settings.method = new_value  # type:ignore

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

    @property
    def grid(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "grid"):
            return typing.cast(SimpleKeyword | None, self._method_settings.grid)
        return None

    @grid.setter
    def grid(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "grid"):
            raise AttributeError("grid is not defined in method_settings object")
        self._method_settings.grid = new_value

    @property
    def scf_maxiter(self) -> int | None:
        if hasattr(self._method_settings, "scf_maxiter"):
            return typing.cast(int | None, self._method_settings.scf_maxiter)
        return None

    @scf_maxiter.setter
    def scf_maxiter(self, new_value: int | None) -> None:
        if not hasattr(self._method_settings, "scf_maxiter"):
            raise AttributeError("scf_maxiter is not defined in method_settings object")
        self._method_settings.scf_maxiter = new_value

    @property
    def scf_threshold(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "scf_threshold"):
            return typing.cast(SimpleKeyword | None, self._method_settings.scf_threshold)
        return None

    @scf_threshold.setter
    def scf_threshold(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "scf_threshold"):
            raise AttributeError("scf_threshold is not defined in method_settings object")
        self._method_settings.scf_threshold = new_value

    @property
    def scf_solver(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "scf_solver"):
            return typing.cast(SimpleKeyword | None, self._method_settings.scf_solver)
        return None

    @scf_solver.setter
    def scf_solver(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "scf_solver"):
            raise AttributeError("scf_solver is not defined in method_settings object")
        self._method_settings.scf_solver = new_value

    @property
    def scf_stab(self) -> bool | None:
        if hasattr(self._method_settings, "scf_stab"):
            return typing.cast(bool | None, self._method_settings.scf_stab)
        return None

    @scf_stab.setter
    def scf_stab(self, new_value: bool | None) -> None:
        if not hasattr(self._method_settings, "scf_stab"):
            raise AttributeError("scf_stab is not defined in method_settings object")
        self._method_settings.scf_stab = new_value

    @property
    def scf_conv(self) -> SimpleKeyword | None:
        if hasattr(self._method_settings, "scf_conv"):
            return typing.cast(SimpleKeyword | None, self._method_settings.scf_conv)
        return None

    @scf_conv.setter
    def scf_conv(self, new_value: str | SimpleKeyword | None) -> None:
        if not hasattr(self._method_settings, "scf_conv"):
            raise AttributeError("scf_conv is not defined in method_settings object")
        self._method_settings.scf_conv = new_value

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
        self._parsed = False

    @staticmethod
    def output_parse(
        func: typing.Callable[[typing.Any], typing.Any],
    ) -> typing.Callable[[typing.Any], typing.Any]:
        """
        Decorator to ensure output parsing is performed before accessing results.

        This decorator wraps methods of a `TaskResults` instance and guarantees
        that the associated output has been parsed before the method is executed.
        Parsing is performed lazily and only once per instance.

        Parameters
        ----------
        func : Callable[[TaskResults], Any]
            The method to wrap. It must be a method of `TaskResults` that relies
            on parsed output data.

        Returns
        -------
        Callable[[TaskResults], Any]
            A wrapped method that ensures `self.output.parse()` has been called
            before delegating to the original function.
        """

        @wraps(func)
        def wrapper(self: "TaskResults") -> typing.Any:
            if not self._parsed:
                self.output.parse()
                self._parsed = True
            return func(self)

        return wrapper

    @cached_property
    def output(self) -> Output:
        if not self.calc_object:
            raise ValueError("calc_object not set")

        return self.calc_object.get_output()

    @cached_property
    def status(self) -> bool:
        return self.output.terminated_normally() and self.output.scf_converged()

    @cached_property
    @abstractmethod
    def primary_property(self) -> typing.Any:
        pass

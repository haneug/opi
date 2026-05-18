import typing
from functools import cached_property
from pathlib import Path

from opi.input import Input
from opi.input.simple_keywords import Goat, SimpleKeyword, Solvent
from opi.input.structures import BaseStructureFile, Properties, Structure
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class GoatSettings(TaskSettings):
    """
    Task settings for GOAT conformer-ensemble explorations (``! GOAT``).

    The boolean flags ``goat_react``, ``goat_diversity``, and
    ``goat_explore`` enable the corresponding ORCA keywords; ``goat_maxiter``
    controls the maximum number of GOAT iterations via ``%goat MaxIter``.
    """

    _name: str = "goat"
    task_keyword: typing.Annotated[SimpleKeyword, Goat] = Goat.GOAT
    goat_maxiter: typing.Annotated[int, "BlockGoat", "maxiter"] | None = None
    goat_react: bool | None = None
    goat_diversity: bool | None = None
    goat_explore: bool | None = None

    def map_to_input(self, input_object: Input) -> Input:
        """
        Extend the base mapping with GOAT-specific keywords.

        Appends ``GOAT_REACT``, ``GOAT_DIVERSITY``, or ``GOAT_EXPLORE`` when
        the corresponding flag is ``True``.

        Parameters
        ----------
        input_object : Input
            ``Input`` object to populate.

        Returns
        -------
        Input
            Modified ``Input`` object.
        """
        super().map_to_input(input_object)

        if self.goat_react:
            input_object.add_simple_keywords(Goat.GOAT_REACT)

        if self.goat_diversity:
            input_object.add_simple_keywords(Goat.GOAT_DIVERSITY)

        if self.goat_explore:
            input_object.add_simple_keywords(Goat.GOAT_EXPLORE)

        return input_object


class GoatTask(SimpleTask):
    """
    High-level task for GOAT conformer-ensemble explorations.

    Returns a ``GoatResults`` object containing the ensemble structures and
    their associated properties read from the ``.finalensemble.xyz`` file.
    """

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

    def run(
        self,
        basename: str,
        struct: Structure | BaseStructureFile,
        working_dir: Path = Path("RUN"),
        ncores: int | None = None,
        memory: int | None = None,
        moinp: Path | None = None,
        strict: bool = False,
    ) -> "GoatResults":
        single_point_result = super().run(
            basename=basename,
            struct=struct,
            working_dir=working_dir,
            ncores=ncores,
            memory=memory,
            moinp=moinp,
            strict=strict,
        )

        return typing.cast(GoatResults, single_point_result)


class GoatResults(TaskResults):
    """Results from a GOAT conformer-ensemble exploration."""

    @cached_property
    def status(self) -> bool:
        """``True`` if the job terminated normally."""
        return self.output.terminated_normally()

    @cached_property
    def structures(self) -> list[Structure]:
        """All structures in the final conformer ensemble."""
        structures = Structure.from_trj_xyz(
            self.output.working_dir / f"{self.output.basename}.finalensemble.xyz"
        )
        return structures

    @cached_property
    def properties(self) -> list[Properties]:
        """Per-conformer properties (energies, …) from the final ensemble file."""
        properties = Properties.from_trj_xyz(
            self.output.working_dir / f"{self.output.basename}.finalensemble.xyz", mode="goat"
        )
        return properties

    @cached_property
    def primary_property(self) -> tuple[list[Structure], list[Properties]]:
        """``(structures, properties)`` tuple for the final conformer ensemble."""
        return self.structures, self.properties

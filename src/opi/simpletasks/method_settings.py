import typing
import warnings

from pydantic import ConfigDict, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo

from opi.input import Input
from opi.input.simple_keywords import (
    AuxBasisSet,
    BasisSet,
    Dft,
    DispersionCorrection,
    ForceField,
    Grid,
    Method,
    SimpleKeyword,
    SolvationModel,
    Solvent,
    Sqm,
    Wft,
)
from opi.input.simple_keywords.dlpno import Dlpno, PNOThresh
from opi.input.simple_keywords.scf import Scf, ScfConvergence, ScfSolver, ScfThreshold
from opi.simpletasks.settings import Settings


class MethodSettings(Settings):
    """
    Base settings class for all computational methods.

    Instantiating ``MethodSettings`` directly dispatches to the appropriate
    subclass (``DFTSettings``, ``SQMSettings``, etc.) based on the ``method``
    keyword via ``__new__``.  Subclasses set ``extra="forbid"`` so that
    unknown fields raise an error at construction time.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra="allow")

    method: typing.Annotated[SimpleKeyword, Method] | None = None
    basis_set: typing.Annotated[SimpleKeyword, BasisSet] | None = None
    solvation_model: typing.Annotated[SimpleKeyword, SolvationModel] | None = None
    solvent: typing.Annotated[str, Solvent] | None = None

    def __new__(cls, /, **data: typing.Any) -> "MethodSettings":
        """
        Dispatch to the correct ``MethodSettings`` subclass.

        When called as ``MethodSettings(method=..., ...)``, inspects ``method``
        and returns an instance of the matching subclass so callers never need
        to import the concrete type.
        """
        if cls is MethodSettings:
            method = data.get("method")
            if method is not None:
                resolved_cls = cls.resolve_method_settings_type(method)
                return super().__new__(resolved_cls)
        return super().__new__(cls)

    @model_validator(mode="before")
    @classmethod
    def _check_valid_fields(cls, data: typing.Any) -> typing.Any:
        """
        Reject unknown fields before Pydantic processes them.

        Subclasses use ``extra="forbid"``, but this pre-validator runs first
        and provides a clearer error message listing both the invalid fields
        and the valid ones.
        """
        if not isinstance(data, dict) or cls is MethodSettings:
            return data
        invalid_fields = set(data) - set(cls.model_fields)
        if invalid_fields:
            field_word = "field" if len(invalid_fields) == 1 else "fields"
            raise ValueError(
                f"Invalid {field_word} for {cls.__name__}: {', '.join(sorted(invalid_fields))}. "
                f"Valid fields: {', '.join(sorted(cls.model_fields))}"
            )
        return data

    @classmethod
    def resolve_method_settings_type(
        cls, method: str | SimpleKeyword
    ) -> typing.Type["MethodSettings"]:
        """
        Return the ``MethodSettings`` subclass that handles ``method``.

        Iterates over the known enum-to-settings mapping and returns the first
        match.

        Parameters
        ----------
        method : str or SimpleKeyword
            Method keyword to look up (e.g. ``"PBE"``, ``"XTB2"``).

        Returns
        -------
        type[MethodSettings]
            Concrete subclass responsible for the given method family.

        Raises
        ------
        ValueError
            If ``method`` is not found in any registered enum.
        """

        enum_to_settings = {
            Dft: DFTSettings,
            Sqm: SQMSettings,
            Wft: WftSettings,
            Method: HFSettings,
            ForceField: ForceFieldSettings,
        }
        for enum_class, settings_type in enum_to_settings.items():
            try:
                if enum_class.find_keyword(method):
                    return typing.cast(typing.Type[MethodSettings], settings_type)
            except ValueError:
                pass

        raise ValueError(f"Keyword {method} not found in any of the valid groupings")


class DFTSettings(MethodSettings):
    """
    Method settings for DFT calculations.

    Accepts DFT functionals with an optional ``-`` separated dispersion
    correction (e.g. ``"PBE-D3BJ"``).  Composite "3c" methods silently drop
    ``basis_set`` because they carry their own basis internally.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "dft"
    method: typing.Annotated[SimpleKeyword, Dft] | None = None
    grid: typing.Annotated[SimpleKeyword, Grid] | None = None
    scf_maxiter: typing.Annotated[int, "BlockScf", "maxiter"] | None = None
    scf_threshold: typing.Annotated[SimpleKeyword, ScfThreshold] | None = None
    scf_solver: typing.Annotated[SimpleKeyword, ScfSolver] | None = None
    scf_stab: bool = False
    scf_conv: typing.Annotated[SimpleKeyword, ScfConvergence] | None = None

    @field_validator("*", mode="before")
    @classmethod
    def validate_fields(cls, value: typing.Any, info: ValidationInfo) -> typing.Any:
        """
        Pre-validate all fields, with special handling for ``method``.

        For the ``method`` field, tries a plain ``Dft`` lookup first; if that
        fails, falls back to ``_find_dft_disp_keyword`` to support
        ``"Functional-Dispersion"`` compound strings.  All other fields
        delegate to the base ``Settings`` validator.
        """
        if info.field_name == "method":
            try:
                new_keyword = Dft.find_keyword(value)
            except ValueError:
                new_keyword = cls._find_dft_disp_keyword(value)
            return new_keyword
        else:
            return super().validate_fields(value, info)

    @model_validator(mode="after")
    def cross_validate(self) -> "DFTSettings":
        """
        Cross-validation for `DftSettings`.
        If the method keyword contains '3c', the `basis_set` attribute will be set to `None`.

        The `DftSettings` object is then returned.
        Parameters
        ----------
        data: DFTSettings
            `DFTSettings` object given as input.

        Returns
        -------
        DFTSettings
            Cross-validated `DFTSettings` object.

        """
        if (self.method and "3c" in self.method.keyword) and self.basis_set:
            warnings.warn("Basis Set will be ignored due to selection of Method", UserWarning)
            self.basis_set = None

        return self

    def map_to_input(self, input_object: Input) -> Input:
        """
        Extend the base mapping with SCF stability analysis.

        Calls the parent ``map_to_input`` for all annotated fields, then
        appends ``SCFSTAB`` when ``scf_stab=True``.

        Parameters
        ----------
        input_object : Input
            ``Input`` object to populate.

        Returns
        -------
        Input
            Modified ``Input`` object.
        """
        input_object = super().map_to_input(input_object)

        if self.scf_stab:
            input_object.add_simple_keywords(Scf.SCFSTAB)

        return input_object

    @classmethod
    def _find_dft_disp_keyword(cls, value: str | SimpleKeyword) -> SimpleKeyword:
        """
        Function to search for a `Dft` keyword along with `DispersionCorrection`.
        In the case that an - is present in keyword, the keyword is split along the - and it is verified whether the
        given keyword is a valid combination of `Dft` and `DispersionCorrection` keyword.

        If it is , a `SimpleKeyword` object is created and returned. If not , a `ValueError` is raised.
        Parameters
        ----------
        value: str | SimpleKeyword
            The value to search for.

        Returns
        -------
        SimpleKeyword
            The created `SimpleKeyword` object.

        Raises
        ------
        ValueError
            If given value is invalid

        """
        if isinstance(value, SimpleKeyword):
            value = value.keyword

        if "-" in value:
            try:
                keywords = value.split("-")
                Dft.find_keyword(keywords[0])
                DispersionCorrection.find_keyword(keywords[1])

                return SimpleKeyword(value)
            except ValueError:
                raise ValueError(f"Invalid Dft keyword or dispersion correction given: {value}")
        else:
            raise ValueError(f"Invalid Dft keyword '{value}'")


class SQMSettings(MethodSettings):
    """
    Method settings for semi-empirical (SQM) calculations.

    Supports the same SCF control knobs as ``DFTSettings`` (``scf_maxiter``,
    ``scf_threshold``, ``scf_solver``, ``scf_stab``, ``scf_conv``).
    No basis set field — SQM methods carry their own parametrisation.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "sqm"
    method: typing.Annotated[SimpleKeyword, Sqm]
    scf_maxiter: typing.Annotated[int, "BlockScf", "maxiter"] | None = None
    scf_threshold: typing.Annotated[SimpleKeyword, ScfThreshold] | None = None
    scf_solver: typing.Annotated[SimpleKeyword, ScfSolver] | None = None
    scf_stab: bool = False
    scf_conv: typing.Annotated[SimpleKeyword, ScfConvergence] | None = None

    def map_to_input(self, input_object: Input) -> Input:
        """
        Extend the base mapping with SCF stability analysis.

        Parameters
        ----------
        input_object : Input
            ``Input`` object to populate.

        Returns
        -------
        Input
            Modified ``Input`` object.
        """
        input_object = super().map_to_input(input_object)

        if self.scf_stab:
            input_object.add_simple_keywords(Scf.SCFSTAB)

        return input_object


class WftSettings(MethodSettings):
    """
    Method settings for wave-function theory (WFT) calculations.

    Covers correlated methods such as MP2, CCSD, CCSD(T), etc.  Basis set
    and solvation are inherited from ``MethodSettings``.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "wft"
    method: typing.Annotated[SimpleKeyword, Wft]


class HFSettings(MethodSettings):
    """
    Method settings for Hartree-Fock calculations.

    Basis set and solvation are inherited from ``MethodSettings``.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "hf"
    method: typing.Annotated[SimpleKeyword, Method]


class ForceFieldSettings(MethodSettings):
    """
    Method settings for force-field calculations.

    ``basis_set`` is silently dropped because force fields do not use a
    quantum-mechanical basis.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "forcefield"
    method: typing.Annotated[SimpleKeyword, ForceField]

    @model_validator(mode="after")
    def cross_validate(self) -> "ForceFieldSettings":
        if self.basis_set:
            warnings.warn(
                "Basis Set will be ignored due to selection of Force Field method", UserWarning
            )
            self.basis_set = None

        return self


class DlpnoCcSettings(MethodSettings):
    """
    Method settings for DLPNO coupled-cluster calculations.

    Exposes DLPNO-specific thresholds (``pno_thresh``, ``dlpno_t_cut_do``,
    ``dlono_t_cut_pno``) and enables LED analysis via ``dlpno_led=True``.
    SCF control knobs are also available.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="forbid"
    )
    _name: str = "dlpnocc"
    method: typing.Annotated[SimpleKeyword, Dft] | None = None
    aux_basis: typing.Annotated[SimpleKeyword, AuxBasisSet] | None = None
    pno_thresh: typing.Annotated[SimpleKeyword, PNOThresh] | None = None
    dlpno_led: bool | None = None
    dlpno_t_cut_do: typing.Annotated[float, "BlockMdci", "tcutdo"] | None = None
    dlono_t_cut_pno: typing.Annotated[float, "BlockMdci", "tcutpno"] | None = None
    scf_maxiter: typing.Annotated[int, "BlockScf", "maxiter"] | None = None
    scf_threshold: typing.Annotated[SimpleKeyword, ScfThreshold] | None = None
    scf_solver: typing.Annotated[SimpleKeyword, ScfSolver] | None = None
    scf_stab: bool = False
    scf_conv: typing.Annotated[SimpleKeyword, ScfConvergence] | None = None

    def map_to_input(self, input_object: Input) -> Input:
        """
        Extend the base mapping with DLPNO-specific keywords.

        Appends ``SCFSTAB`` when ``scf_stab=True`` and ``LED`` when
        ``dlpno_led=True``, in addition to the standard field-annotation
        mapping performed by the parent.

        Parameters
        ----------
        input_object : Input
            ``Input`` object to populate.

        Returns
        -------
        Input
            Modified ``Input`` object.
        """
        input_object = super().map_to_input(input_object)

        if self.scf_stab:
            input_object.add_simple_keywords(Scf.SCFSTAB)

        if self.dlpno_led:
            input_object.add_simple_keywords(Dlpno.LED)

        return input_object

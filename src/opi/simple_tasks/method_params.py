"""Method-family parameter objects for the SimpleTasks feature.

This module provides the concrete :class:`~opi.simple_tasks.base.TaskParams`
subclasses (:class:`DftParams`, :class:`SqmParams`, :class:`WftParams`,
:class:`ForceFieldParams`) and the :func:`get_params_for_method` factory that
selects the right one at run time.

Method-family detection is done via the OPI keyword class hierarchy rather
than a hard-coded dictionary: each family class (:class:`~opi.input.simple_keywords.dft.Dft`,
:class:`~opi.input.simple_keywords.wft.Wft`, etc.) knows its own members, so
the lookup stays automatically in sync as new keywords are added to OPI.

Users never import these classes directly; they are selected and instantiated
by :meth:`~opi.simple_tasks.base.Task.run`.
"""

from __future__ import annotations

import warnings

from opi.input.simple_keywords.base import SimpleKeyword
from opi.simple_tasks.base import TaskParams

__all__ = (
    "DftParams",
    "ForceFieldParams",
    "SqmParams",
    "WftParams",
    "get_params_for_method",
    "resolve_method_family",
)


# ---------------------------------------------------------------------------
# Concrete parameter classes
# ---------------------------------------------------------------------------


class DftParams(TaskParams):
    """Method-family parameters for density-functional theory calculations.

    The method and basis-set keywords are added to the
    :class:`~opi.input.core.Input` by
    :meth:`~opi.simple_tasks.base.Task.get_input` before
    :meth:`map_to_input` is called.  This class currently holds no fields;
    it is a stub ready for future extension.

    Notes
    -----
    Future extensions — dispersion correction, RI approximation, grid
    settings — should be added as ``Annotated`` fields following the
    metadata pattern documented in :class:`~opi.simple_tasks.base.TaskParams`.
    """


class SqmParams(TaskParams):
    """Method-family parameters for semi-empirical / tight-binding calculations.

    Semi-empirical methods (GFN2-xTB, AM1, …) carry an implicit basis set;
    no ``basis_set`` keyword is required or added.  This class currently holds
    no fields; it is a stub ready for future extension.

    Notes
    -----
    Future extensions — xTB ``%xtb`` block options, accuracy settings —
    should be added as ``Annotated`` fields following the metadata pattern
    documented in :class:`~opi.simple_tasks.base.TaskParams`.
    """


class WftParams(TaskParams):
    """Method-family parameters for wave-function theory calculations.

    Wave-function methods (HF, MP2, CCSD(T), …) generally require an
    explicit basis set supplied via
    :attr:`~opi.simple_tasks.base.Task.basis_set`.  This class currently holds
    no fields; it is a stub ready for future extension.

    Notes
    -----
    Future extensions — frozen-core settings, RI auxiliary basis, MDCI
    block options — should be added as ``Annotated`` fields following the
    metadata pattern documented in :class:`~opi.simple_tasks.base.TaskParams`.
    """


class ForceFieldParams(TaskParams):
    """Method-family parameters for force-field calculations.

    Force-field methods (GFN-FF, MM) do not require a basis set.
    This class currently holds no fields; it is a stub ready for future
    extension.

    Notes
    -----
    Future extensions should be added as ``Annotated`` fields following the
    metadata pattern documented in :class:`~opi.simple_tasks.base.TaskParams`.
    """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_method_family(method: str) -> str:
    """Return the method-family string for *method*.

    Queries each family class in order using its
    :meth:`~opi.input.simple_keywords.base.SimpleKeywordBox.find_keyword`
    method.  Unknown methods default to ``"dft"`` and emit a
    :class:`UserWarning`.

    Parameters
    ----------
    method : str
        Method name to look up (case-insensitive, e.g. ``"BP86"``,
        ``"GFN2-xTB"``).

    Returns
    -------
    str
        One of ``"dft"``, ``"sqm"``, ``"wft"``, or ``"ff"``.
    """
    # Deferred imports keep the module loadable before the keyword hierarchy
    # is fully initialised and avoid any circular-import risk.
    from opi.input.simple_keywords.dft import Dft  # noqa: PLC0415
    from opi.input.simple_keywords.force_field import ForceField  # noqa: PLC0415
    from opi.input.simple_keywords.sqm import Sqm  # noqa: PLC0415
    from opi.input.simple_keywords.wft import Wft  # noqa: PLC0415

    for family_cls, family_name in (
        (Dft, "dft"),
        (Wft, "wft"),
        (Sqm, "sqm"),
        (ForceField, "ff"),
    ):
        try:
            family_cls.find_keyword(method)
            return family_name
        except ValueError:
            pass

    warnings.warn(
        f"Method {method!r} is not in the OPI method-family registry. "
        "Defaulting to DFT.",
        stacklevel=3,
    )
    return "dft"


def get_params_for_method(
    method: SimpleKeyword,
) -> DftParams | SqmParams | WftParams | ForceFieldParams:
    """Return the appropriate :class:`~opi.simple_tasks.base.TaskParams` for *method*.

    Uses :func:`resolve_method_family` to detect the family and instantiates
    the matching param class.

    Parameters
    ----------
    method : SimpleKeyword
        Normalised method keyword as stored on a
        :class:`~opi.simple_tasks.base.Task` instance.

    Returns
    -------
    DftParams | SqmParams | WftParams | ForceFieldParams
        A method-family parameter object.  Call
        :meth:`~opi.simple_tasks.base.TaskParams.map_to_input` on the
        returned object to apply any family-specific settings to an
        :class:`~opi.input.core.Input`.
    """
    from opi.input.simple_keywords.dft import Dft  # noqa: PLC0415
    from opi.input.simple_keywords.force_field import ForceField  # noqa: PLC0415
    from opi.input.simple_keywords.sqm import Sqm  # noqa: PLC0415
    from opi.input.simple_keywords.wft import Wft  # noqa: PLC0415

    keyword = method.keyword

    for family_cls, params_cls in (
        (Dft, DftParams),
        (Wft, WftParams),
        (Sqm, SqmParams),
        (ForceField, ForceFieldParams),
    ):
        try:
            family_cls.find_keyword(keyword)
            return params_cls()
        except ValueError:
            pass

    warnings.warn(
        f"Could not determine method family for {keyword!r}. Defaulting to DFT.",
        stacklevel=3,
    )
    return DftParams()

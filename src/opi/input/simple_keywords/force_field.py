from opi.input.simple_keywords.base import SimpleKeyword
from opi.input.simple_keywords.method import Method

__all__ = ("ForceField",)


class ForceField(Method):
    """Enum to store all simple keywords of type ForceField."""

    GFN_FF = SimpleKeyword("gfn-ff")
    """SimpleKeyword: GFN-FF (external) alias is xtb-ff."""
    MM = SimpleKeyword("mm")
    """SimpleKeyword: Use external molecular mechanics."""

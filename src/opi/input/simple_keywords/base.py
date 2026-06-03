__all__ = ("SimpleKeyword", "SimpleKeywordBox")


class SimpleKeywordBox:
    """
    Base class for groups of related ``SimpleKeyword`` constants.

    Each concrete subclass (e.g. ``Task``, ``Dft``, ``BasisSet``) declares its
    members as class-level ``SimpleKeyword`` attributes.
    """

    @classmethod
    def from_string(cls, s: str) -> "SimpleKeyword":
        """
        Look up a ``SimpleKeyword`` by string across all registered subclasses.

        Matching is case-insensitive and checks the keyword value, the
        attribute name, and the optional alias — in that order.

        Raises
        ------
        ValueError
            If no matching keyword is found in the registry.
        """
        norm = s.lower()

        # Here the function will loop over all attributes both existing and inherited by the current class.
        # The simple keywords are structured such that, for example, the larger `Scf` grouping is a child class of the semantically smaller groupings,
        # such as `ScfConvergence`, `ScfThreshold` and so on.
        for attr in dir(cls):
            # Get the value associated with attribute
            simple_keyword = getattr(cls, attr)
            if attr.startswith("_") or not isinstance(
                simple_keyword, SimpleKeyword
            ):  # Skip private/magic attributes or non-Simple Keyword attributes
                continue
            # Case 1: if the user searches for keyword through how it would appear in ORCA input
            if simple_keyword.keyword.lower() == norm:
                return simple_keyword
            # Case 2: if the user searches for keyword through how it is stored in OPI
            elif attr.lower() == norm:
                return simple_keyword
            # Case 3: if the user searches for keyword through a known alias
            elif simple_keyword.alias and any(a.lower() == norm for a in simple_keyword.alias):
                return simple_keyword

        # In the case that no matches are found, raise ValueError
        raise ValueError(f"Keyword {s} not found in class {cls.__name__}")

    @classmethod
    def find_keyword(cls, inp: "SimpleKeyword | str") -> "SimpleKeyword":
        """
        Resolve a string or ``SimpleKeyword`` to a registered ``SimpleKeyword``.

        Accepts a bare string or an existing ``SimpleKeyword`` (whose ``.keyword``
        string is used for the lookup).

        Raises
        ------
        ValueError
            If ``inp`` is not a str or SimpleKeyword, or if the string is not
            found in the registry.
        """
        # If input is SimpleKeyword, convert to string representation
        if isinstance(inp, SimpleKeyword):
            inp = inp.keyword

        if not isinstance(inp, str):
            raise ValueError(
                f"{cls.__name__} expects a str or SimpleKeyword, got {type(inp).__name__}: {inp!r}"
            )

        return cls.from_string(inp)


class SimpleKeyword:
    """
    A single ORCA simple keyword (e.g. ``SP``, ``PBE``, ``def2-SVP``).

    Instances are used as typed constants inside ``SimpleKeywordBox`` subclasses
    and can also be constructed directly from a raw string for ad-hoc keywords.

    Attributes
    ----------
    keyword : str
        The keyword string as it will appear in the ORCA ``.inp`` file.
    alias : list[str] | None
        Optional alternative name(s) accepted by ``SimpleKeywordBox.from_string``.
    """

    _keyword: str
    alias: list[str] | None = None

    def __init__(self, keyword: str, alias: str | list[str] | None = None) -> None:
        """
        Parameters
        ----------
        keyword : str
            Keyword string for the ORCA input line. Leading/trailing whitespace
            is stripped; an empty string raises ``ValueError``.
        alias : str, optional
            Alternative lookup name for ``SimpleKeywordBox.from_string``.
        """
        self.keyword = keyword
        self.alias = [alias] if isinstance(alias, str) else alias

    @property
    def keyword(self) -> str:
        return self._keyword

    @keyword.setter
    def keyword(self, value: str) -> None:
        """
        Parameters
        ----------
        value : str
        """
        if not isinstance(value, str):
            raise TypeError(f"{self.__class__.__name__}.keyword: must of type str!")
        # > Stripping trailing whitespaces
        value = value.rstrip()
        if not value:
            raise ValueError(
                f"{self.__class__.__name__}.keyword: must contain more than just whitespaces!"
            )
        self._keyword = value

    def format_orca(self) -> str:
        """
        Function to format simple keyword for ORCA input file

        Returns
        -------
        str
            Formatted string for ORCA input file
        """
        return self.keyword.lower()

    def __hash__(self) -> int:
        return self.keyword.__hash__()

    def __str__(self) -> str:
        return self.format_orca()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimpleKeyword):
            return False
        return self.keyword == other.keyword

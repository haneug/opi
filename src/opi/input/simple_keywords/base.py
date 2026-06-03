__all__ = ("SimpleKeyword", "SimpleKeywordBox")


class SimpleKeywordBox:
    """
    Registry base class for groups of related ``SimpleKeyword`` constants.

    Each concrete subclass (e.g. ``Task``, ``Dft``, ``BasisSet``) declares its
    members as class-level ``SimpleKeyword`` attributes.  Subclassing
    automatically registers the new class so that ``from_string`` can search
    across all members in the group.
    """

    _registry: list[type["SimpleKeywordBox"]] = []

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
            value = getattr(cls, attr)
            if attr.startswith("_") or not isinstance(
                value, SimpleKeyword
            ):  # Skip private/magic attributes or non-Simple Keyword attributes
                continue
            # Case 1: if the user searches for keyword through how it would appear in ORCA input
            if value.keyword.lower() == norm:
                return value
            # Case 2: if the user searches for keyword through how it is stored in OPI
            elif attr.lower() == norm:
                return value
            # Case 3: if the user searches for keyword through a known alias
            elif value.alias and value.alias.lower() == norm:
                return value

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
    alias : str or None
        Optional alternative name accepted by ``SimpleKeywordBox.from_string``.
    """

    alias: str | None = None

    def __init__(self, keyword: str, alias: str | None = None) -> None:
        """
        Parameters
        ----------
        keyword : str
            Keyword string for the ORCA input line. Leading/trailing whitespace
            is stripped; an empty string raises ``ValueError``.
        alias : str, optional
            Alternative lookup name for ``SimpleKeywordBox.from_string``.
        """
        self._keyword: str = ""
        self.keyword = keyword
        self._name: str = ""
        self.alias = alias

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

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Parameters
        ----------
        value : str
        """
        if not isinstance(value, str):
            raise TypeError(f"{self.__class__.__name__}.name: must be of type str!")
        # > Stripping trailing whitespaces
        value = value.rstrip()
        if not value:
            raise ValueError(
                f"{self.__class__.__name__}.name: must contain more than just whitespaces!"
            )
        self._name = value

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

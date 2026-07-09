"""Parse a potential FCIDUMP file"""

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import numpy as np


@dataclass
class Fcidump:
    """
    Reads and stores data from a FCIDUMP file. One and two-electrons integrals are stored as dicts and can be
    accessed as numpy arrays via `hcore_matrix` and `eri_tensor`.

    Attributes
    --------
    norb: int
        Number of active orbitals.
    nelec: int
        Number of active electrons.
    ms2: int
        Electron spin multiplicity.
    orbsym: int
        Symmetry labels of the orbitals.
    isym: int
        Overall symmetry of the electronic structure.
    one_electron: dict[tuple[int, int], float]
        Dictionary that contains the one-electron integrals.
    two_electron: dict[tuple[int, int, int, int], float]
        Dictionary that contains the two-electron integrals.
    e_nuc: float
        Electronic core contribution. Contains the contracted energy of the inactive space.
    path: Path
        Path to the FCIDUMP file.
    """

    norb: int
    nelec: int
    ms2: int
    orbsym: list[int]
    isym: int
    one_electron: dict[tuple[int, int], float] = field(default_factory=dict)
    two_electron: dict[tuple[int, int, int, int], float] = field(default_factory=dict)
    e_nuc: float = 0.0
    path: Path = field(default_factory=Path)

    @cached_property
    def hcore_matrix(self) -> np.ndarray:
        """Return the one-electron integrals as a symmetric (norb, norb) numpy array."""
        mat = np.zeros((self.norb, self.norb))
        for (i, j), val in self.one_electron.items():
            mat[i - 1, j - 1] = val
            mat[j - 1, i - 1] = val
        return mat

    @cached_property
    def eri_tensor(self) -> np.ndarray:
        """Return the two-electron integrals as a (norb, norb, norb, norb) numpy array.

        Uses chemist's notation (ij|kl) with 8-fold permutation symmetry applied.
        """
        tensor = np.zeros((self.norb,) * 4)

        # > Pull all stored indices/values into arrays once
        idx = np.array(list(self.two_electron.keys()), dtype=np.int64) - 1  # (norb, 4)
        vals = np.array(list(self.two_electron.values()), dtype=np.float64)  # (norb,)
        a, b, c, d = idx[:, 0], idx[:, 1], idx[:, 2], idx[:, 3]

        # > Build all 8 permutations as stacked index arrays
        perms = [
            (a, b, c, d),
            (b, a, c, d),
            (a, b, d, c),
            (b, a, d, c),
            (c, d, a, b),
            (d, c, a, b),
            (c, d, b, a),
            (d, c, b, a),
        ]
        # > Concatenate the different permutations of the index arrays
        p = np.concatenate([p[0] for p in perms])
        q = np.concatenate([p[1] for p in perms])
        r = np.concatenate([p[2] for p in perms])
        s = np.concatenate([p[3] for p in perms])
        # > Set up a value array with the same 8 x norb dimension
        v = np.tile(vals, 8)

        # > Vectorized generation of the eri array
        tensor[p, q, r, s] = v
        return tensor

    @classmethod
    def from_file(cls, path: Path | str) -> "Fcidump":
        """
        Parse a FCIDUMP file and return the populated `Fcidump` object.
        The FCIDUMP file is documented in the paper:
        Knowles, P. J.; Handy, N. C. A Determinant Based Full Configuration Interaction Program.
        Computer Physics Communications 1989, 54, 75–83. https://doi.org/10.1016/0010-4655(89)90033-7

        Raises
        -------
        ValueError
            If the FCIDUMP file cannot be parsed.
        FileNotFoundError
            If the FCIDUMP file cannot be found at the given path.
        """
        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(f"{cls.__name__}: FCIDUMP file not found at {path}")

        text = path.read_text()

        # > Split header and body
        end_match = re.search(r"&END|/", text, re.IGNORECASE)
        if end_match is None:
            raise ValueError(
                f"{cls.__name__}: Could not find header terminator (&END or /) in {path}"
            )
        header = text[: end_match.end()]
        body = text[end_match.end() :]

        # > Parse the header
        dump = cls(
            norb=cls._get_int("NORB", header),
            nelec=cls._get_int("NELEC", header),
            ms2=cls._get_int("MS2", header),
            orbsym=cls._get_int_list("ORBSYM", header),
            isym=cls._get_int("ISYM", header),
            path=Path(path),
        )

        # > Parse the integrals from the body
        for line in body.splitlines():
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 5:
                raise ValueError(f"{cls.__name__}: Could not parse {line} in {path}")
            try:
                val, i, j, k, ll = (
                    float(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                    int(parts[3]),
                    int(parts[4]),
                )
            except ValueError:
                raise ValueError(f"{cls.__name__}: Could not parse {line} in {path}")
            # > Inactive contribution
            if i == 0 and j == 0 and k == 0 and ll == 0:
                dump.e_nuc = val
            # > One-electron matrix
            elif k == 0 and ll == 0:
                dump.one_electron[(i, j)] = val
            # > Two-electron tensor
            else:
                dump.two_electron[(i, j, k, ll)] = val

        return dump

    @classmethod
    def _get_int(cls, key: str, header: str) -> int:
        """Return the positive integer value of the given key."""
        m = re.search(rf"{key}\s*=\s*(\d+)", header, re.IGNORECASE)
        if m is None:
            raise ValueError(f"{cls.__name__}: Could not parse {key}")
        return int(m.group(1))

    @classmethod
    def _get_int_list(cls, key: str, header: str) -> list[int]:
        """Return a list of integers corresponding to the given key."""
        m = re.search(rf"{key}\s*=\s*(\d+(\s*,\s*\d+)+)", header, re.IGNORECASE)
        if m is None:
            raise ValueError(f"{cls.__name__}: Could not parse {key}")
        return [int(x) for x in re.split(r"[,\s]+", m.group(1).strip()) if x]

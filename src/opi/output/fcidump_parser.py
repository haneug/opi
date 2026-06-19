"""Parse a potential FCIDUMP file"""

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import numpy as np


@dataclass
class Fcidump:
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
        """Return the one-electron integrals as a symmetric (norb, norb) matrix."""
        mat = np.zeros((self.norb, self.norb))
        for (i, j), val in self.one_electron.items():
            mat[i - 1, j - 1] = val
            mat[j - 1, i - 1] = val
        return mat

    @cached_property
    def eri_tensor(self) -> np.ndarray:
        """Return the two-electron integrals as a (norb, norb, norb, norb) tensor.

        Uses chemist's notation (ij|kl) with 8-fold permutation symmetry applied.
        """
        tensor = np.zeros((self.norb,) * 4)
        # > use ll instead of l to satisfy ruff
        for (i, j, k, ll), val in self.two_electron.items():
            a, b, c, d = i - 1, j - 1, k - 1, ll - 1
            for p, q, r, s in [
                (a, b, c, d),
                (b, a, c, d),
                (a, b, d, c),
                (b, a, d, c),
                (c, d, a, b),
                (d, c, a, b),
                (c, d, b, a),
                (d, c, b, a),
            ]:
                tensor[p, q, r, s] = val
        return tensor

    @classmethod
    def parse_fcidump(cls, path: Path | str) -> "Fcidump":

        if isinstance(path, str):
            path = Path(path)

        with open(path) as f:
            text = f.read()

        # Split header and body
        end_match = re.search(r"&END|/", text, re.IGNORECASE)
        if end_match is None:
            raise ValueError(f"Could not find header terminator (&END or /) in {path}")
        header = text[: end_match.end()]
        body = text[end_match.end() :]

        # Parse header fields
        def get_int(key: str) -> int:
            m = re.search(rf"{key}\s*=\s*(\d+)", header, re.IGNORECASE)
            return int(m.group(1)) if m else 0

        def get_int_list(key: str) -> list[int]:
            m = re.search(rf"{key}\s*=\s*([\d,\s]+)", header, re.IGNORECASE)
            return [int(x) for x in re.split(r"[,\s]+", m.group(1).strip()) if x] if m else []

        dump = cls(
            norb=get_int("NORB"),
            nelec=get_int("NELEC"),
            ms2=get_int("MS2"),
            orbsym=get_int_list("ORBSYM"),
            isym=get_int("ISYM"),
            path=Path(path),
        )

        # Parse integral lines
        for line in body.splitlines():
            parts = line.split()
            if len(parts) != 5:
                continue
            val, i, j, k, ll = (
                float(parts[0]),
                int(parts[1]),
                int(parts[2]),
                int(parts[3]),
                int(parts[4]),
            )
            if i == 0 and j == 0 and k == 0 and ll == 0:
                dump.e_nuc = val
            elif k == 0 and ll == 0:
                dump.one_electron[(i, j)] = val
            else:
                dump.two_electron[(i, j, k, ll)] = val

        return dump

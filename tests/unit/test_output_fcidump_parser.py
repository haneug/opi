import textwrap
from pathlib import Path

import pytest

from opi.output.fcidump import Fcidump


@pytest.mark.unit
def test_parse_fcidump_header(tmp_path: Path) -> None:
    fcidump_text = textwrap.dedent("""\
         &FCI
          NORB= 2, NELEC= 2, MS2= 0,
          ORBSYM=1,1,
          ISYM=0,
         /
          0.5000000000  1  1  1  1
          0.1000000000  2  1  1  1
          0.2000000000  2  2  1  1
          0.3000000000  2  2  2  2
         -0.1234567890  1  1  0  0
          0.0987654321  2  1  0  0
          0.0500000000  2  2  0  0
         -1.2345678901  0  0  0  0
    """)
    fci_file = tmp_path / "test.fcidump"
    fci_file.write_text(fcidump_text)

    dump = Fcidump.from_file(fci_file)

    assert dump.norb == 2
    assert dump.nelec == 2
    assert dump.ms2 == 0
    assert dump.orbsym == [1, 1]
    assert dump.isym == 0
    assert pytest.approx(dump.e_nuc) == -1.2345678901


@pytest.mark.unit
def test_hcore_matrix_shape_and_symmetry() -> None:
    dump = Fcidump(
        norb=2,
        nelec=2,
        ms2=0,
        orbsym=[1, 1],
        isym=0,
        one_electron={(1, 1): -0.5, (2, 1): 0.1, (2, 2): -0.3},
    )
    mat = dump.hcore_matrix

    assert mat.shape == (2, 2)
    assert pytest.approx(mat[0, 0]) == -0.5
    assert pytest.approx(mat[1, 1]) == -0.3
    # off-diagonal must be symmetric
    assert pytest.approx(mat[1, 0]) == 0.1
    assert pytest.approx(mat[0, 1]) == 0.1


@pytest.mark.unit
def test_eri_tensor_shape_and_symmetry() -> None:
    dump = Fcidump(
        norb=2,
        nelec=2,
        ms2=0,
        orbsym=[1, 1],
        isym=0,
        two_electron={(1, 1, 1, 1): 0.5, (2, 1, 1, 1): 0.1, (2, 2, 1, 1): 0.2, (2, 2, 2, 2): 0.3},
    )
    tensor = dump.eri_tensor

    assert tensor.shape == (2, 2, 2, 2)
    assert pytest.approx(tensor[0, 0, 0, 0]) == 0.5
    assert pytest.approx(tensor[1, 1, 1, 1]) == 0.3
    # check 8-fold symmetry for (2,1,1,1) -> index (1,0,0,0)
    val = 0.1
    assert pytest.approx(tensor[1, 0, 0, 0]) == val  # (ij|kl)
    assert pytest.approx(tensor[0, 1, 0, 0]) == val  # (ji|kl)
    assert pytest.approx(tensor[0, 0, 1, 0]) == val  # (kl|ij)
    assert pytest.approx(tensor[0, 0, 0, 1]) == val  # (lk|ij)

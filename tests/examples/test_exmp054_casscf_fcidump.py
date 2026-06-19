import numpy as np
import pytest

from examples.exmp054_casscf_fcidump.job import run_exmp054
from opi.input.structures import Structure


@pytest.mark.examples
@pytest.mark.orca
def test_exmp054_casscf_fcidump(example_input_file, tmp_path) -> None:
    """Test the FCIDUMP export from a CASSCF calculation."""
    # Get input file from example folder
    input_file = example_input_file(run_exmp054)
    structure = Structure.from_xyz(input_file)

    # Run the example in tmp_path
    output = run_exmp054(structure=structure, working_dir=tmp_path)

    fcidump = output.get_fcidump()
    assert fcidump is not None

    fcidump_file = fcidump.path
    assert fcidump_file.exists() and fcidump_file.is_file()

    norb = fcidump.norb
    assert fcidump.hcore_matrix.shape == (norb, norb)
    assert fcidump.eri_tensor.shape == (norb, norb, norb, norb)

    # hcore must be symmetric
    assert np.allclose(fcidump.hcore_matrix, fcidump.hcore_matrix.T)
    # eri must satisfy (ij|kl) == (kl|ij)
    assert np.allclose(fcidump.eri_tensor, fcidump.eri_tensor.transpose(2, 3, 0, 1))

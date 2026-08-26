from pathlib import Path

import pytest

from opi.output.core import Output
from opi.output.vcd_mode import VcdMode

"""
Unit tests for the VCD getter of the Output class

The VCD spectrum is only available from the plain-text output file, so these tests work on a
minimal excerpt of a real ORCA output instead of a JSON fixture.
"""

# > Excerpt of the VCD block of an ORCA output, followed by the line that ends the block
_VCD_BLOCK = """\
------------------------------------------------------------------------------
                     ORCA SPECTROSCOPIC PROPERTIES CALCULATION
------------------------------------------------------------------------------

VCD SPECTRUM CALCULATION
------------------------

Calculating the atomic axial tensor (analytic) ... done ( 0.023 sec)

---------------------------------
 Mode   Freq    VCD-Intensity
       (1/cm) (1E-44*esu^2*cm^2)
---------------------------------
    6   211.4         -4.39
    7   368.3         14.52
   12   965.0         46.23

Maximum memory used throughout the entire PROP-calculation: 39.0 MB
"""


@pytest.fixture
def output_with_vcd(tmp_path: Path) -> Output:
    """Output object whose .out file contains a VCD block."""
    (tmp_path / "job.out").write_text(_VCD_BLOCK)
    output = Output("job", version_check=False)
    output.working_dir = tmp_path
    return output


@pytest.mark.unit
@pytest.mark.output
def test_vcd_mode_from_string():
    """Test if `VcdMode.from_string()` parses a line of the ORCA VCD block."""
    mode = VcdMode.from_string("   12   965.0         46.23")

    assert mode.mode == 12
    assert mode.wavenumber == pytest.approx(965.0)
    assert mode.intensity == pytest.approx(46.23)


@pytest.mark.unit
@pytest.mark.output
def test_get_vcd_returns_modes(output_with_vcd):
    """Test if `Output.get_vcd()` greps the VCD block and stops at the end of the table."""
    vcd = output_with_vcd.get_vcd()

    # > The block must end at the empty line, not run into the following text
    assert sorted(vcd) == [6, 7, 12]
    assert vcd[6].intensity == pytest.approx(-4.39)
    assert vcd[12].wavenumber == pytest.approx(965.0)


@pytest.mark.unit
@pytest.mark.output
def test_get_vcd_returns_none(tmp_path: Path):
    """Test if `Output.get_vcd()` returns None if the output holds no VCD spectrum."""
    (tmp_path / "job.out").write_text("****ORCA TERMINATED NORMALLY****\n")
    output = Output("job", version_check=False)
    output.working_dir = tmp_path

    assert output.get_vcd() is None

from opi.models.string_enum import StringEnum


class EnergyType(StringEnum):
    """
    Enumeration of the energy types that `Output.get_energies()` is known to return.

    The members are the keys of the dictionary returned by `Output.get_energies()`, so they can be
    used for the lookup directly, e.g. `output.get_energies()[EnergyType.MDCI_SD_T]`.

    ORCA names the energy types itself, hence this enumeration is not exhaustive: the dictionary is
    keyed by plain strings and a calculation may well produce a type that is not listed here.
    """

    UNKNOWN = "Unknown"
    """No information about the energy is provided."""
    SCF = "SCF"
    """SCF energy from HF, DFT or SQM methods."""
    MP2 = "MP2"
    """MP2 energy."""
    MP2_OO = "MP2(OO)"
    """Orbital-optimised MP2 energy."""
    MDCI_SD = "MDCI(SD)"
    """Typically the (DLPNO-)CCSD energy."""
    MDCI_SD_T = "MDCI(SD(T))"
    """Typically the (DLPNO-)CCSD(T) energy."""
    CASSCF = "CASSCF"
    """CASSCF energy."""
    CASSCF_PT2 = "CASSCF IC-PT2: NEVPT2/CASPT2"
    """Internally contracted PT2 energy on top of a CASSCF reference."""
    AUTOCI = "AUTOCI"
    """Energy of an automatically generated CI calculation."""
    TDA_CIS = "TDA/CIS"
    """TDA-TD-DFT or CIS energy."""
    VDW = "VdW"
    """Dispersion correction, see `Output.get_vdw_correction()`."""
    GCP = "gCP"
    """Geometrical counterpoise correction, see `Output.get_gcp_correction()`."""

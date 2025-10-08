import numpy as np

from app.server.ir_units import IRMeta, to_A10


def test_transmittance_to_A10():
    A10, _ = to_A10(np.array([1.0, 0.1]), IRMeta(yunits="Transmittance", yfactor=1.0))
    assert np.allclose(A10, [0.0, 1.0])


def test_percent_T_to_A10():
    A10, _ = to_A10(np.array([100.0, 10.0]), IRMeta(yunits="%Transmittance", yfactor=1.0))
    assert np.allclose(A10, [0.0, 1.0])


def test_absorbance_e_to_A10():
    A10, _ = to_A10(np.array([2.303]), IRMeta(yunits="Absorbance (base e)", yfactor=1.0))
    assert np.isclose(A10[0], 1.0, atol=1e-12)


def test_alpha10_requires_params():
    try:
        to_A10(
            np.array([1e-6]),
            IRMeta(yunits="(µmol/mol)^-1 m^-1 (base 10)", yfactor=1.0),
        )
        assert False
    except ValueError:
        assert True


def test_alpha10_to_A10_ok():
    A10, _ = to_A10(
        np.array([1e-6]),
        IRMeta(
            yunits="(µmol/mol)^-1 m^-1 (base 10)",
            yfactor=1.0,
            path_m=10.0,
            mole_fraction=50e-6,
        ),
    )
    assert np.isclose(A10[0], 1e-6 * 50e-6 * 10.0)

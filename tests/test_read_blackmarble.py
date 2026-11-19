"""Leitor Black Marble. O HDF5 aqui e SINTETICO: imita nomes de SDS, fill e flags do
VNP46A4 v2.0 (conforme inspecao do arquivo real), mas contem valores arbitrarios."""
import h5py
import numpy as np
import pytest

from openlux.io import read_blackmarble

GRID = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields"
LAYER = "AllAngle_Composite_Snow_Free"


@pytest.fixture
def h5file(tmp_path):
    p = tmp_path / "synthetic.h5"
    rad = np.array([[1.0, 2.0, -999.9], [3.0, -0.5, 5.0], [6.0, 7.0, 8.0]], dtype="float32")
    qual = np.array([[0, 0, 255], [1, 0, 0], [0, 0, 0]], dtype="uint8")
    num = np.array([[10, 10, 65535], [10, 10, 2], [10, 10, 10]], dtype="uint16")
    lw = np.array([[1, 1, 1], [1, 1, 1], [3, 2, 1]], dtype="uint8")
    with h5py.File(p, "w") as f:
        f.attrs["HorizontalTileNumber"] = 13
        f.attrs["VerticalTileNumber"] = 11
        g = f.create_group(GRID)
        g[LAYER] = rad
        g[LAYER + "_Quality"] = qual
        g[LAYER + "_Num"] = num
        g["Land_Water_Mask"] = lw
    return p


def test_masks_and_transform(h5file):
    arr, t = read_blackmarble(h5file, LAYER, n_min=5)
    assert (t.c, t.f) == (-50.0, -20.0)
    expected = np.array([[1.0, 2.0, np.nan],      # fill -> NaN
                         [np.nan, np.nan, np.nan],  # qualidade 1 ; negativo ; n<5
                         [np.nan, np.nan, 8.0]],  # mar ; agua interna ; ok
                        dtype="float32")
    np.testing.assert_array_equal(arr, expected)


def test_poor_quality_can_be_allowed_as_sensitivity(h5file):
    arr, _ = read_blackmarble(h5file, LAYER, n_min=1, allowed_quality=(0, 1))
    assert arr[1, 0] == 3.0
    assert np.isnan(arr[1, 1])  # negativo continua invalido


def test_rejects_non_hdf5(tmp_path):
    from openlux.io import InvalidDownload
    p = tmp_path / "x.h5"
    p.write_text("<html>")
    with pytest.raises(InvalidDownload):
        read_blackmarble(p, LAYER)

from unittest.mock import MagicMock, patch

import pytest

from cura.BuildVolume import BuildVolume
import numpy

@pytest.fixture
def build_volume():
    mocked_application = MagicMock()
    mocked_platform = MagicMock(name="platform")
    with patch("cura.BuildVolume.Platform", mocked_platform):
        return BuildVolume(mocked_application)


def test_buildVolumeSetSizes(build_volume):
    build_volume.setWidth(10)
    assert build_volume.getDiagonalSize() == 10

    build_volume.setWidth(0)
    build_volume.setHeight(100)
    assert build_volume.getDiagonalSize() == 100

    build_volume.setHeight(0)
    build_volume.setDepth(200)
    assert build_volume.getDiagonalSize() == 200


def test_buildMesh(build_volume):
    mesh = build_volume._buildMesh(0, 100, 0, 100, 0, 100, 1)
    result_vertices = numpy.array([[0., 0., 0.], [100., 0., 0.], [0., 0., 0.], [0., 100., 0.], [0., 100., 0.], [100., 100., 0.], [100., 0., 0.], [100., 100., 0.], [0., 0., 100.], [100., 0., 100.], [0., 0., 100.], [0., 100., 100.], [0., 100., 100.], [100., 100., 100.], [100., 0., 100.], [100., 100., 100.], [0., 0., 0.], [0., 0., 100.], [100., 0., 0.], [100., 0., 100.], [0., 100., 0.], [0., 100., 100.], [100., 100., 0.], [100., 100., 100.]], dtype=numpy.float32)
    assert numpy.array_equal(result_vertices, mesh.getVertices())


def test_buildGridMesh(build_volume):
    mesh = build_volume._buildGridMesh(0, 100, 0, 100, 0, 100, 1)
    result_vertices = numpy.array([[0., -1., 0.], [100., -1., 100.], [100., -1., 0.], [0., -1., 0.], [0., -1., 100.], [100., -1., 100.]])
    assert numpy.array_equal(result_vertices, mesh.getVertices())

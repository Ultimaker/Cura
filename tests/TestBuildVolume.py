from unittest.mock import MagicMock, patch

import pytest

from UM.Math.Polygon import Polygon
from UM.Settings.SettingInstance import InstanceState
from cura.BuildVolume import BuildVolume, PRIME_CLEARANCE
import numpy




@pytest.fixture
def build_volume() -> BuildVolume:
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


class TestComputeDisallowedAreasPrimeBlob:
    setting_property_dict = {"machine_width": {"value": 50},
                             "machine_depth": {"value": 100},
                             "prime_blob_enable": {"value": True},
                             "extruder_prime_pos_x":  {"value": 25},
                             "extruder_prime_pos_y": {"value": 50},
                             "machine_center_is_zero": {"value": True},
                             }

    def getPropertySideEffect(*args, **kwargs):
        properties = TestComputeDisallowedAreasPrimeBlob.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def test_noGlobalContainer(self, build_volume: BuildVolume):
        # No global container and no extruders, so we expect no blob areas
        assert build_volume._computeDisallowedAreasPrimeBlob(12, []) == {}

    def test_noExtruders(self, build_volume: BuildVolume):
        mocked_stack = MagicMock()
        mocked_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_stack
        # No extruders, so still expect that we get no area
        assert build_volume._computeDisallowedAreasPrimeBlob(12, []) == {}

    def test_singleExtruder(self, build_volume: BuildVolume):
        mocked_global_stack = MagicMock(name = "mocked_global_stack")
        mocked_global_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        mocked_extruder_stack = MagicMock(name = "mocked_extruder_stack")
        mocked_extruder_stack.getId = MagicMock(return_value = "0")
        mocked_extruder_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_global_stack

        # Create a polygon that should be the result
        resulting_polygon = Polygon.approximatedCircle(PRIME_CLEARANCE)
        # Since we want a blob of size 12;
        resulting_polygon = resulting_polygon.getMinkowskiHull(Polygon.approximatedCircle(12))
        # In the The translation result is 25, -50 (due to the settings used)
        resulting_polygon = resulting_polygon.translate(25, -50)
        assert build_volume._computeDisallowedAreasPrimeBlob(12, [mocked_extruder_stack]) == {"0": [resulting_polygon]}

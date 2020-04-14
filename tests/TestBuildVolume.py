from unittest.mock import MagicMock, patch
import pytest

from UM.Math.Polygon import Polygon
from UM.Math.Vector import Vector
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


def test_clamp(build_volume):
    assert build_volume._clamp(0, 0, 200) == 0
    assert build_volume._clamp(0, -200, 200) == 0
    assert build_volume._clamp(300, -200, 200) == 200


class TestCalculateBedAdhesionSize:
    setting_property_dict = {"adhesion_type": {"value": "brim"},
                             "skirt_brim_line_width": {"value": 0},
                             "initial_layer_line_width_factor": {"value": 0},
                             "brim_line_count": {"value": 0},
                             "machine_width": {"value": 200},
                             "machine_depth": {"value": 200},
                             "skirt_line_count": {"value": 0},
                             "skirt_gap": {"value": 0},
                             "raft_margin": {"value": 0}
                             }

    def getPropertySideEffect(*args, **kwargs):
        properties = TestCalculateBedAdhesionSize.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def createAndSetGlobalStack(self, build_volume):
        mocked_stack = MagicMock()
        mocked_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_stack

    def test_noGlobalStack(self, build_volume: BuildVolume):
        assert build_volume._calculateBedAdhesionSize([]) is None

    @pytest.mark.parametrize("setting_dict, result", [
        ({}, 0),
        ({"adhesion_type": {"value": "skirt"}}, 0),
        ({"adhesion_type": {"value": "raft"}}, 0),
        ({"adhesion_type": {"value": "none"}}, 0),
        ({"adhesion_type": {"value": "skirt"}, "skirt_line_count": {"value": 2}, "initial_layer_line_width_factor": {"value": 1}, "skirt_brim_line_width": {"value": 2}}, 0.02),
        # Even though it's marked as skirt, it should behave as a brim as the prime tower has a brim (skirt line count is still at 0!)
        ({"adhesion_type": {"value": "skirt"}, "prime_tower_brim_enable": {"value": True}, "skirt_brim_line_width": {"value": 2}, "initial_layer_line_width_factor": {"value": 3}}, -0.06),
        ({"brim_line_count": {"value": 1}, "skirt_brim_line_width": {"value": 2}, "initial_layer_line_width_factor": {"value": 3}}, 0),
        ({"brim_line_count": {"value": 2}, "skirt_brim_line_width": {"value": 2}, "initial_layer_line_width_factor": {"value": 3}}, 0.06),
        ({"brim_line_count": {"value": 9000000}, "skirt_brim_line_width": {"value": 90000}, "initial_layer_line_width_factor": {"value": 9000}}, 100),  # Clamped at half the max size of buildplate
    ])
    def test_singleExtruder(self, build_volume: BuildVolume, setting_dict, result):
        self.createAndSetGlobalStack(build_volume)
        patched_dictionary = self.setting_property_dict.copy()
        patched_dictionary.update(setting_dict)
        with patch.dict(self.setting_property_dict, patched_dictionary):
            assert build_volume._calculateBedAdhesionSize([]) == result

    def test_unknownBedAdhesion(self, build_volume: BuildVolume):
        self.createAndSetGlobalStack(build_volume)
        patched_dictionary = self.setting_property_dict.copy()
        patched_dictionary.update({"adhesion_type": {"value": "OMGZOMGBBQ"}})
        with patch.dict(self.setting_property_dict, patched_dictionary):
            with pytest.raises(Exception):
                build_volume._calculateBedAdhesionSize([])

class TestComputeDisallowedAreasStatic:
    setting_property_dict = {"machine_disallowed_areas": {"value": [[[-200,  112.5], [ -82,  112.5], [ -84,  102.5], [-115,  102.5]]]},
                             "machine_width": {"value": 200},
                             "machine_depth": {"value": 200},
                            }

    def getPropertySideEffect(*args, **kwargs):
        properties = TestComputeDisallowedAreasStatic.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def test_computeDisallowedAreasStaticNoExtruder(self, build_volume: BuildVolume):
        mocked_stack = MagicMock()
        mocked_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_stack
        assert build_volume._computeDisallowedAreasStatic(0, []) == {}

    def test_computeDisalowedAreasStaticSingleExtruder(self, build_volume: BuildVolume):
        mocked_stack = MagicMock()
        mocked_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        mocked_extruder = MagicMock()
        mocked_extruder.getProperty = MagicMock(side_effect=self.getPropertySideEffect)
        mocked_extruder.getId = MagicMock(return_value = "zomg")

        build_volume._global_container_stack = mocked_stack
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
            result = build_volume._computeDisallowedAreasStatic(0, [mocked_extruder])
            assert result == {"zomg": [Polygon([[-84.0, 102.5], [-115.0, 102.5], [-200.0, 112.5], [-82.0, 112.5]])]}

    def test_computeDisalowedAreasMutliExtruder(self, build_volume):
        mocked_stack = MagicMock()
        mocked_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        mocked_extruder = MagicMock()
        mocked_extruder.getProperty = MagicMock(side_effect=self.getPropertySideEffect)
        mocked_extruder.getId = MagicMock(return_value="zomg")
        extruder_manager = MagicMock()
        extruder_manager.getActiveExtruderStacks = MagicMock(return_value = [mocked_stack])
        build_volume._global_container_stack = mocked_stack
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value = extruder_manager)):
            result = build_volume._computeDisallowedAreasStatic(0, [mocked_extruder])
            assert result == {"zomg": [Polygon([[-84.0, 102.5], [-115.0, 102.5], [-200.0, 112.5], [-82.0, 112.5]])]}

class TestUpdateRaftThickness:
    setting_property_dict = {"raft_base_thickness": {"value": 1},
                             "raft_interface_thickness": {"value": 1},
                             "raft_surface_layers": {"value": 1},
                             "raft_surface_thickness": {"value": 1},
                             "raft_airgap": {"value": 1},
                             "layer_0_z_overlap": {"value": 1},
                             "adhesion_type": {"value": "raft"}}

    def getPropertySideEffect(*args, **kwargs):
        properties = TestUpdateRaftThickness.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def createMockedStack(self):
        mocked_global_stack = MagicMock(name="mocked_global_stack")
        mocked_global_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)
        extruder_stack = MagicMock()

        mocked_global_stack.extruders = {"0": extruder_stack}

        return mocked_global_stack

    def test_simple(self, build_volume: BuildVolume):
        build_volume.raftThicknessChanged = MagicMock()
        mocked_global_stack = self.createMockedStack()
        build_volume._global_container_stack = mocked_global_stack

        assert build_volume.getRaftThickness() == 0
        build_volume._updateRaftThickness()
        assert build_volume.getRaftThickness() == 3
        assert build_volume.raftThicknessChanged.emit.call_count == 1

    def test_adhesionIsNotRaft(self, build_volume: BuildVolume):
        patched_dictionary = self.setting_property_dict.copy()
        patched_dictionary["adhesion_type"] = {"value": "not_raft"}

        mocked_global_stack = self.createMockedStack()
        build_volume._global_container_stack = mocked_global_stack

        assert build_volume.getRaftThickness() == 0
        with patch.dict(self.setting_property_dict, patched_dictionary):
            build_volume._updateRaftThickness()
        assert build_volume.getRaftThickness() == 0

    def test_noGlobalStack(self, build_volume: BuildVolume):
        build_volume.raftThicknessChanged = MagicMock()
        assert build_volume.getRaftThickness() == 0
        build_volume._updateRaftThickness()
        assert build_volume.getRaftThickness() == 0
        assert build_volume.raftThicknessChanged.emit.call_count == 0


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


class TestCalculateExtraZClearance:
    setting_property_dict = {"retraction_hop": {"value": 12},
                             "retraction_hop_enabled": {"value": True}}

    def getPropertySideEffect(*args, **kwargs):
        properties = TestCalculateExtraZClearance.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def test_noContainerStack(self, build_volume: BuildVolume):
        assert build_volume._calculateExtraZClearance([]) is 0

    def test_withRetractionHop(self, build_volume: BuildVolume):
        mocked_global_stack = MagicMock(name="mocked_global_stack")

        mocked_extruder = MagicMock()
        mocked_extruder.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_global_stack

        # It should be 12 because we have the hop enabled and the hop distance is set to 12
        assert build_volume._calculateExtraZClearance([mocked_extruder]) == 12

    def test_withoutRetractionHop(self, build_volume: BuildVolume):
        mocked_global_stack = MagicMock(name="mocked_global_stack")

        mocked_extruder = MagicMock()
        mocked_extruder.getProperty = MagicMock(side_effect=self.getPropertySideEffect)

        build_volume._global_container_stack = mocked_global_stack

        patched_dictionary = self.setting_property_dict.copy()
        patched_dictionary["retraction_hop_enabled"] = {"value": False}
        with patch.dict(self.setting_property_dict, patched_dictionary):
            # It should be 12 because we have the hop enabled and the hop distance is set to 12
            assert build_volume._calculateExtraZClearance([mocked_extruder]) == 0


class TestRebuild:
    def test_zeroWidthHeightDepth(self, build_volume: BuildVolume):
        build_volume.rebuild()
        assert build_volume.getMeshData() is None

    def test_engineIsNotRead(self, build_volume: BuildVolume):
        build_volume.setWidth(10)
        build_volume.setHeight(10)
        build_volume.setDepth(10)
        build_volume.rebuild()
        assert build_volume.getMeshData() is None

    def test_noGlobalStack(self, build_volume: BuildVolume):
        build_volume.setWidth(10)
        build_volume.setHeight(10)
        build_volume.setDepth(10)
        # Fake the the "engine is created callback"
        build_volume._onEngineCreated()
        build_volume.rebuild()
        assert build_volume.getMeshData() is None

    def test_updateBoundingBox(self, build_volume: BuildVolume):
        build_volume.setWidth(10)
        build_volume.setHeight(10)
        build_volume.setDepth(10)

        mocked_global_stack = MagicMock()
        build_volume._global_container_stack = mocked_global_stack
        build_volume.getEdgeDisallowedSize = MagicMock(return_value = 0)
        build_volume.updateNodeBoundaryCheck = MagicMock()

        # Fake the the "engine is created callback"
        build_volume._onEngineCreated()
        build_volume.rebuild()

        bounding_box = build_volume.getBoundingBox()
        assert bounding_box.minimum == Vector(-5.0, -1.0, -5.0)
        assert bounding_box.maximum == Vector(5.0, 10.0, 5.0)


class TestUpdateMachineSizeProperties:
    setting_property_dict = {"machine_width": {"value": 50},
                             "machine_depth": {"value": 100},
                             "machine_height": {"value": 200},
                             "machine_shape": {"value": "DERP!"}}

    def getPropertySideEffect(*args, **kwargs):
        properties = TestUpdateMachineSizeProperties.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def test_noGlobalStack(self, build_volume: BuildVolume):
        build_volume._updateMachineSizeProperties()
        assert build_volume._width == 0
        assert build_volume._height == 0
        assert build_volume._depth == 0
        assert build_volume._shape == ""

    def test_happy(self, build_volume: BuildVolume):
        mocked_global_stack = MagicMock(name="mocked_global_stack")
        mocked_global_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)
        build_volume._global_container_stack = mocked_global_stack
        build_volume._updateMachineSizeProperties()
        assert build_volume._width == 50
        assert build_volume._height == 200
        assert build_volume._depth == 100
        assert build_volume._shape == "DERP!"


class TestGetEdgeDisallowedSize:
    setting_property_dict = {}
    bed_adhesion_size = 1

    @pytest.fixture()
    def build_volume(self, build_volume):
        build_volume._calculateBedAdhesionSize = MagicMock(return_value = 1)
        return build_volume

    def getPropertySideEffect(*args, **kwargs):
        properties = TestGetEdgeDisallowedSize.setting_property_dict.get(args[1])
        if properties:
            return properties.get(args[2])

    def createMockedStack(self):
        mocked_global_stack = MagicMock(name="mocked_global_stack")
        mocked_global_stack.getProperty = MagicMock(side_effect=self.getPropertySideEffect)
        return mocked_global_stack

    def test_noGlobalContainer(self, build_volume: BuildVolume):
        assert build_volume.getEdgeDisallowedSize() == 0

    def test_unknownAdhesion(self, build_volume: BuildVolume):
        build_volume._global_container_stack = self.createMockedStack()
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
            #with pytest.raises(Exception):
                # Since we don't have any adhesion set, this should break.

            build_volume.getEdgeDisallowedSize()

    def test_oneAtATime(self, build_volume: BuildVolume):
        build_volume._global_container_stack = self.createMockedStack()
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
            with patch.dict(self.setting_property_dict, {"print_sequence": {"value": "one_at_a_time"}}):
                assert build_volume.getEdgeDisallowedSize() == 0.1


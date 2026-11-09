from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy
import pytest

from SimulationView.SimulationView import SimulationView
from cura.LayerPolygon import LayerPolygon


class Node:
    def __init__(self, data = None):
        self.data = data
        self.children = []

    def getChildren(self):
        return self.children

    def getAllChildren(self):
        return [descendant for child in self.children for descendant in [child, *child.getAllChildren()]]

    def callDecoration(self, name):
        assert name == "getLayerData"
        return self.data


class LayerData:
    def __init__(self, feedrate = 20):
        self.scans = 0
        self.layer = SimpleNamespace(polygons=[SimpleNamespace(
            types=numpy.array([LayerPolygon.SkinType]),
            lineFeedrates=numpy.array([feedrate], dtype=float),
            lineWidths=numpy.array([.4]), lineThicknesses=numpy.array([.2]),
        )])

    def getLayers(self):
        self.scans += 1
        return {0: self.layer}

    def getLayer(self, number):
        return self.layer


def make_view():
    data = LayerData()
    root = Node()
    root.children.append(Node(data))
    visibility = [True, False, False, False]
    view = SimpleNamespace(
        _color_scheme_data_sources=None, _color_scheme_visibility=None,
        getController=lambda: SimpleNamespace(getScene=lambda: SimpleNamespace(getRoot=lambda: root)),
        getShowSkin=lambda: visibility[0], getShowInfill=lambda: visibility[1],
        getShowHelpers=lambda: visibility[2], getShowTravelMoves=lambda: visibility[3],
        colorSchemeLimitsChanged=MagicMock(),
    )
    for name in ("feedrate", "line_width", "thickness", "flow_rate"):
        setattr(view, "_min_" + name, 0)
        setattr(view, "_max_" + name, 0)
    return view, root, data, visibility


def test_visual_scene_changes_do_not_rescan_layers():
    view, root, data, _ = make_view()
    SimulationView.calculateColorSchemeLimits(view)
    assert view._max_feedrate == 20
    for _ in range(100):
        root.children.append(Node())
        SimulationView.calculateColorSchemeLimits(view)
        root.children.pop()
    assert data.scans == 1
    view.colorSchemeLimitsChanged.emit.assert_called_once_with()


@pytest.mark.parametrize("flag", range(4))
def test_visibility_changes_invalidate_statistics(flag):
    view, _, data, visibility = make_view()
    SimulationView.calculateColorSchemeLimits(view)
    visibility[flag] = not visibility[flag]
    SimulationView.calculateColorSchemeLimits(view)
    assert data.scans == 2


def test_new_slice_invalidates_statistics():
    view, root, data, _ = make_view()
    SimulationView.calculateColorSchemeLimits(view)
    replacement = LayerData(40)
    root.children[0].data = replacement
    SimulationView.calculateColorSchemeLimits(view)
    assert view._max_feedrate == 40
    assert replacement.scans == 1


def test_removing_layer_data_clears_statistics():
    view, root, _, _ = make_view()
    SimulationView.calculateColorSchemeLimits(view)
    root.children.clear()
    SimulationView.calculateColorSchemeLimits(view)
    assert view._color_scheme_data_sources == ()

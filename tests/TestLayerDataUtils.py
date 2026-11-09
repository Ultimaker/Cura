from types import SimpleNamespace

from cura.LayerDataUtils import has_printed_layer


NON_PRINTING_TYPES = {0, 8, 9, 12, 13}


def test_zero_height_layer_is_not_printable():
    layer = SimpleNamespace(
        height=0,
        polygons=[SimpleNamespace(types=[1])],
    )

    assert not has_printed_layer(layer, NON_PRINTING_TYPES)


def test_travel_only_layer_is_not_printable():
    layer = SimpleNamespace(
        height=5,
        polygons=[SimpleNamespace(types=[8, 9, 12, 13])],
    )

    assert not has_printed_layer(layer, NON_PRINTING_TYPES)


def test_layer_with_extrusion_is_printable():
    layer = SimpleNamespace(
        height=0.2,
        polygons=[SimpleNamespace(types=[8, 1, 9])],
    )

    assert has_printed_layer(layer, NON_PRINTING_TYPES)

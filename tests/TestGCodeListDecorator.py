from cura.Scene.GCodeListDecorator import GCodeListDecorator


def test_setAndGetList():
    decorator = GCodeListDecorator()

    decorator.setGCodeList(["Test"])
    assert decorator.getGCodeList() == ["Test"]


def test_copyGCodeDecorator():
    decorator = GCodeListDecorator()
    decorator.setGCodeList(["Test"])
    import copy
    copied_decorator = copy.deepcopy(decorator)
    assert decorator.getGCodeList() == copied_decorator.getGCodeList()

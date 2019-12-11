import configparser

import VersionUpgrade43to44

before_update = """[general]
version = 4
name = Ultimaker 3
id = Ultimaker 3

[metadata]
type = machine

[containers]
0 = user_profile
1 = quality_changes
2 = quality
3 = material
4 = variant
5 = definition_changes
6 = definition
"""


def test_upgrade():
    upgrader = VersionUpgrade43to44.VersionUpgrade43to44()
    file_name, new_data =  upgrader.upgradeStack(before_update, "whatever")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(new_data[0])
    assert parser["containers"]["0"] == "user_profile"
    assert parser["containers"]["1"] == "quality_changes"
    assert parser["containers"]["2"] == "empty_intent"
    assert parser["containers"]["3"] == "quality"
    assert parser["containers"]["4"] == "material"
    assert parser["containers"]["5"] == "variant"
    assert parser["containers"]["6"] == "definition_changes"
    assert parser["containers"]["7"] == "definition"
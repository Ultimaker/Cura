# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest #To register tests with.

from LegacyProfileReader import LegacyProfileReader #The module we're testing.

@pytest.fixture
def legacy_profile_reader():
    return LegacyProfileReader()

test_prepareDefaultsData = [
    {
        "defaults": {
            "foo": "bar"
        },
        "cheese": "delicious"
    },
    {
        "cat": "fluffy",
        "dog": "floofy"
    }
]

@pytest.mark.parametrize("input", test_prepareDefaultsData)
def test_prepareDefaults(legacy_profile_reader, input):
    output = legacy_profile_reader.prepareDefaults(input)
    if "defaults" in input:
        assert input["defaults"] == output
    else:
        assert output == {}
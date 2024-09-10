# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest
from unittest.mock import MagicMock

from plugins.CuraEngineBackend.StartSliceJob import GcodeStartEndFormatter


# def createMockedInstanceContainer(container_id):
#     result = MagicMock()
#     result.getId = MagicMock(return_value=container_id)
#     result.getMetaDataEntry = MagicMock(side_effect=getMetadataEntrySideEffect)
#     return result

class MockValueProvider:
    ##  Creates a mock value provider.
    #
    #   This initialises a dictionary with key-value pairs.
    def __init__(self, values):
        self._values = values

    ##  Provides a value.
    #
    #   \param name The key of the value to provide.
    def getProperty(self, key, property_name, context = None):
        if not (key in self._values):
            return None
        return self._values[key]

extruder_0_values = {
    "material_temperature": 190.0
}

extruder_1_values = {
    "material_temperature": 210.0
}

global_values = {
    "bed_temperature": 50.0,
    "initial_extruder": 0
}

extruder_0_provider = MockValueProvider(extruder_0_values)
extruder_1_provider = MockValueProvider(extruder_1_values)

all_extruder_settings = {"-1": global_values, "0": extruder_0_values, "1": extruder_1_values}

test_cases = [
    ('Static code', 'G0', 'G0'),

    ('Basic replacement', 'M128 {bed_temperature}', 'M128 50.0'),

    (
        'Conditional expression with global setting',
'''{if bed_temperature > 30}
G123
{else}
G456
{endif}''',
'''G123
'''
    ),

    (
        'Conditional expression with extruder setting directly specified by index 0',
'''{if material_temperature > 200, 0}
G10
{else}
G20
{endif}''',
'''G20
'''
    ),
    (
        'Conditional expression with extruder setting directly specified by index 1',
'''{if material_temperature > 200, 1}
G100
{else}
G200
{endif}''',
'''G100
'''
    ),

    (
        'Conditional expression with extruder index specified by setting',
'''{if material_temperature > 200, initial_extruder}
G1000
{else}
G2000
{endif}''',
'''G2000
'''
    ),

    (
        'Conditional expression with extruder index specified by formula',
'''{if material_temperature > 200, (initial_extruder + 1) % 2}
X1000
{else}
X2000
{endif}''',
'''X1000
'''
    ),

    (
        'Conditional expression with elsif',
'''{if bed_temperature < 30}
T30
{elif bed_temperature >= 30 and bed_temperature < 40}
T40
{elif bed_temperature >= 40 and bed_temperature < 50}
T50
{elif bed_temperature >= 50 and bed_temperature < 60}
T60
{elif bed_temperature >= 60 and bed_temperature < 70}
T70
{else}
T-800
{endif}''',
'''T60
'''
    ),

    (
        'Formula inside a conditional expression',
'''{if bed_temperature < 30}
Z000
{else}
Z{bed_temperature + 10}
{endif}''',
'''Z60.0
'''
    ),

    (
        'Other commands around conditional expression',
'''
R000
# My super initial command
R111 X123 Y456 Z789
{if bed_temperature > 30}
R987
R654 X321
{else}
R963 X852 Y741
R321 X654 Y987
{endif}
# And finally, the end of the start at the beginning of the header
R369
R357 X951 Y843''',
'''
R000
# My super initial command
R111 X123 Y456 Z789
R987
R654 X321
# And finally, the end of the start at the beginning of the header
R369
R357 X951 Y843'''
    ),

    (
        'Multiple conditional expressions',
'''
A999
{if bed_temperature > 30}
A000
{else}
A100
{endif}
A888
{if material_temperature > 200, 0}
A200
{else}
A300
{endif}
A777
''',
'''
A999
A000
A888
A300
A777
'''
    ),
]

def pytest_generate_tests(metafunc):
    if "original_gcode" in metafunc.fixturenames:
        tests_ids = [test[0] for test in test_cases]
        tests_data = [test[1:] for test in test_cases]
        metafunc.parametrize("original_gcode, expected_gcode", tests_data, ids = tests_ids)

@pytest.fixture
def cura_application():
    result = MagicMock()
    result.getGlobalContainerStack = MagicMock(return_value = MockValueProvider(global_values))
    return result

@pytest.fixture
def extruder_manager():
    def get_extruder(extruder_nr: str):
        if extruder_nr == "0":
            return extruder_0_provider
        elif extruder_nr == "1":
            return extruder_1_provider
        else:
            return None

    result = MagicMock()
    result.getExtruderStack = MagicMock(side_effect = get_extruder)
    return result

def test_startEndGCode_replace(cura_application, extruder_manager, original_gcode, expected_gcode):
    formatter = GcodeStartEndFormatter(all_extruder_settings, -1)
    formatter._cura_application = cura_application
    formatter._extruder_manager = extruder_manager
    assert formatter.format(original_gcode) == expected_gcode

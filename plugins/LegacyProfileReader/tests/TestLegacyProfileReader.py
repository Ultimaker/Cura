# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser # An input for some functions we're testing.
import pytest # To register tests with.

from LegacyProfileReader import LegacyProfileReader # The module we're testing.

@pytest.fixture
def legacy_profile_reader():
    return LegacyProfileReader()

test_prepareDefaultsData = [
    {
        "defaults":
        {
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

test_prepareLocalsData = [
    ( # Ordinary case.
        { # Parser data.
            "profile":
            {
                "layer_height": "0.2",
                "infill_density": "30"
            }
        },
        "profile", # Config section.
        { # Defaults.
            "layer_height": "0.1",
            "infill_density": "20",
            "line_width": "0.4"
        }
    ),
    ( # Empty data.
        { # Parser data.
            "profile":
            {
            }
        },
        "profile", # Config section.
        { # Defaults.
        }
    ),
    ( # All defaults.
        { # Parser data.
            "profile":
            {
            }
        },
        "profile", # Config section.
        { # Defaults.
            "foo": "bar",
            "boo": "far"
        }
    ),
    ( # Multiple config sections.
        { # Parser data.
            "some_other_name":
            {
                "foo": "bar"
            },
            "profile":
            {
                "foo": "baz" #Not the same as in some_other_name
            }
        },
        "profile", # Config section.
        { # Defaults.
            "foo": "bla"
        }
    ),
    ( # Section does not exist.
        { # Parser data.
            "some_other_name":
            {
                "foo": "bar"
            },
        },
        "profile", # Config section.
        { # Defaults.
            "foo": "baz"
        }
    )
]

@pytest.mark.parametrize("parser_data, config_section, defaults", test_prepareLocalsData)
def test_prepareLocals(legacy_profile_reader, parser_data, config_section, defaults):
    parser = configparser.ConfigParser()
    parser.read_dict(parser_data)

    output = legacy_profile_reader.prepareLocals(parser, config_section, defaults)

    assert set(defaults.keys()) <= set(output.keys()) # All defaults must be in there.
    assert set(parser_data[config_section]) <= set(output.keys()) # All overwritten values must be in there.
    for key in output:
        if key in parser_data[config_section]:
            assert output[key] == parser_data[config_section][key] # If overwritten, must be the overwritten value.
        else:
            assert output[key] == defaults[key] # Otherwise must be equal to the default.
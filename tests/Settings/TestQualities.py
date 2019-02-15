# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import pytest

from UM.Settings.InstanceContainer import InstanceContainer

import os
import os.path


def collectAllQualities():
    result = []
    for root, directories, filenames in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "quality"))):
        for filename in filenames:
            result.append(os.path.join(root, filename))
    return result


def collecAllDefinitionIds():
    result = []
    for root, directories, filenames in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions"))):
        for filename in filenames:
            result.append(os.path.basename(filename).split(".")[0])
    return result


all_definition_ids = collecAllDefinitionIds()
quality_filepaths = collectAllQualities()


##  Atempt to load all the quality types
@pytest.mark.parametrize("file_name", quality_filepaths)
def test_validateQualityProfiles(file_name):
    try:
        with open(file_name, encoding="utf-8") as data:
            json = data.read()
            result = InstanceContainer._readAndValidateSerialized(json)
            # Fairly obvious, but all the types here should be of the type quality
            assert InstanceContainer.getConfigurationTypeFromSerialized(json) == "quality"
            # All quality profiles must be linked to an existing definition.
            assert result["general"]["definition"] in all_definition_ids

    except Exception as e:
        # File can't be read, header sections missing, whatever the case, this shouldn't happen!
        print("Go an Exception while reading he file [%s]: %s" % (file_name, e))
        assert False

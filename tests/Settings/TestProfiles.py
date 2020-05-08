# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from unittest.mock import MagicMock
import configparser  # To read the profiles.
import os
import os.path
import pytest

from cura.CuraApplication import CuraApplication  # To compare against the current SettingVersion.
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.VersionUpgradeManager import VersionUpgradeManager


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


def collectAllSettingIds():
    VersionUpgradeManager._VersionUpgradeManager__instance = VersionUpgradeManager(MagicMock())

    CuraApplication._initializeSettingDefinitions()

    definition_container = DefinitionContainer("whatever")
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions", "fdmprinter.def.json"), encoding = "utf-8") as data:
        definition_container.deserialize(data.read())
    return definition_container.getAllKeys()


def collectAllVariants():
    result = []
    for root, directories, filenames in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "variants"))):
        for filename in filenames:
            result.append(os.path.join(root, filename))
    return result

def collectAllIntents():
    result = []
    for root, directories, filenames in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "intent"))):
        for filename in filenames:
            result.append(os.path.join(root, filename))
    return result

all_definition_ids = collecAllDefinitionIds()
quality_filepaths = collectAllQualities()
all_setting_ids = collectAllSettingIds()
variant_filepaths = collectAllVariants()
intent_filepaths = collectAllIntents()


##  Attempt to load all the quality profiles.
@pytest.mark.parametrize("file_name", quality_filepaths)
def test_validateQualityProfiles(file_name):
    try:
        with open(file_name, encoding = "utf-8") as data:
            serialized = data.read()
            result = InstanceContainer._readAndValidateSerialized(serialized)
            # Fairly obvious, but all the types here should be of the type quality
            assert InstanceContainer.getConfigurationTypeFromSerialized(serialized) == "quality"
            # All quality profiles must be linked to an existing definition.
            assert result["general"]["definition"] in all_definition_ids

            # We don't care what the value is, as long as it's there.
            assert result["metadata"].get("quality_type", None) is not None

            # Check that all the values that we say something about are known.
            if "values" in result:
                quality_setting_keys = set(result["values"])
                # Prune all the comments from the values
                quality_setting_keys = {key for key in quality_setting_keys if not key.startswith("#")}

                has_unknown_settings = not quality_setting_keys.issubset(all_setting_ids)
                if has_unknown_settings:
                    print("The following setting(s) %s are defined in the quality %s, but not in fdmprinter.def.json" % ([key for key in quality_setting_keys if key not in all_setting_ids], file_name))
                    assert False

    except Exception as e:
        # File can't be read, header sections missing, whatever the case, this shouldn't happen!
        print("Got an Exception while reading the file [%s]: %s" % (file_name, e))
        assert False

@pytest.mark.parametrize("file_name", intent_filepaths)
def test_validateIntentProfiles(file_name):
    try:
        with open(file_name, encoding = "utf-8") as f:
            serialized = f.read()
            result = InstanceContainer._readAndValidateSerialized(serialized)
            assert InstanceContainer.getConfigurationTypeFromSerialized(serialized) == "intent", "The intent folder must only contain intent profiles."
            assert result["general"]["definition"] in all_definition_ids, "The definition for this intent profile must exist."
            assert result["metadata"].get("intent_category", None) is not None, "All intent profiles must have some intent category."
            assert result["metadata"].get("quality_type", None) is not None, "All intent profiles must be linked to some quality type."
            assert result["metadata"].get("material", None) is not None, "All intent profiles must be linked to some material."
            assert result["metadata"].get("variant", None) is not None, "All intent profiles must be linked to some variant."

            # Check that all the values that we say something about are known.
            if "values" in result:
                intent_setting_keys = set(result["values"])
                unknown_settings = intent_setting_keys - all_setting_ids
                assert len(unknown_settings) == 0, "The settings {setting_list} are defined in the intent {file_name}, but not in fdmprinter.def.json".format(setting_list = unknown_settings, file_name = file_name)
    except Exception as e:
        # File can't be read, header sections missing, whatever the case, this shouldn't happen!
        assert False, "Got an exception while reading the file {file_name}: {err}".format(file_name = file_name, err = str(e))

##  Attempt to load all the variant profiles.
@pytest.mark.parametrize("file_name", variant_filepaths)
def test_validateVariantProfiles(file_name):
    try:
        with open(file_name, encoding = "utf-8") as data:
            serialized = data.read()
            result = InstanceContainer._readAndValidateSerialized(serialized)
            # Fairly obvious, but all the types here should be of the type quality
            assert InstanceContainer.getConfigurationTypeFromSerialized(serialized) == "variant"
            # All quality profiles must be linked to an existing definition.
            assert result["general"]["definition"] in all_definition_ids

            # Check that all the values that we say something about are known.
            if "values" in result:
                variant_setting_keys = set(result["values"])
                # Prune all the comments from the values
                variant_setting_keys = {key for key in variant_setting_keys if not key.startswith("#")}

                has_unknown_settings = not variant_setting_keys.issubset(all_setting_ids)
                if has_unknown_settings:
                    print("The following setting(s) %s are defined in the variant %s, but not in fdmprinter.def.json" % ([key for key in variant_setting_keys if key not in all_setting_ids], file_name))
                    assert False
    except Exception as e:
        # File can't be read, header sections missing, whatever the case, this shouldn't happen!
        print("Got an Exception while reading the file [%s]: %s" % (file_name, e))
        assert False

@pytest.mark.parametrize("file_name", quality_filepaths + variant_filepaths + intent_filepaths)
def test_versionUpToDate(file_name):
    try:
        with open(file_name, encoding = "utf-8") as data:
            parser = configparser.ConfigParser(interpolation = None)
            parser.read(file_name)

            assert "general" in parser
            assert "version" in parser["general"]
            assert int(parser["general"]["version"]) == InstanceContainer.Version

            assert "metadata" in parser
            assert "setting_version" in parser["metadata"]
            assert int(parser["metadata"]["setting_version"]) == CuraApplication.SettingVersion
    except Exception as e:
        # File can't be read, header sections missing, whatever the case, this shouldn't happen!
        print("Got an exception while reading the file {file_name}: {err}".format(file_name = file_name, err = str(e)))
        assert False
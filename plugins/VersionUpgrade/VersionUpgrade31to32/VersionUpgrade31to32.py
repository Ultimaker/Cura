# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.
import os
from urllib.parse import quote_plus

from UM.Resources import Resources
from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

from cura.CuraApplication import CuraApplication


class VersionUpgrade31to32(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 3.0 format.
    #
    #   Since the format may change, this is implemented for the 3.0 format only
    #   and needs to be included in the version upgrade system rather than
    #   globally in Uranium.
    #
    #   \param serialised The serialised form of a CFG file.
    #   \return The version number stored in the CFG file.
    #   \raises ValueError The format of the version number in the file is
    #   incorrect.
    #   \raises KeyError The format of the file is incorrect.
    def getCfgVersion(self, serialised):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = 0))
        return format_version * 1000000 + setting_version

    ##  Upgrades a preferences file from version 3.1 to 3.2.
    #
    #   \param serialised The serialised form of a preferences file.
    #   \param filename The name of the file to upgrade.
    def upgradePreferences(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        # Update version numbers
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "5"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades a container stack from version 3.1 to 3.2.
    #
    #   \param serialised The serialised form of a container stack.
    #   \param filename The name of the file to upgrade.
    def upgradeStack(self, serialised, filename):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        # Update version numbers

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "5"

        # Re-serialise the file.
        output = io.StringIO()
        parser.write(output)
        return [filename], [output.getvalue()]

    ##  Upgrades the given instance container file from version 3.1 to 3.2.
    #
    #   \param serialised The serialised form of the container file.
    #   \param filename The name of the file to upgrade.
    def upgradeInstanceContainer(self, serialised, filename):

        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialised)

        if parser["metadata"]["type"] == "definition_changes":
            if parser["general"]["definition"] == "custom":

                # We are only interested in machine_nozzle_size
                if parser.has_option("values", "machine_nozzle_size"):
                    machine_nozzle_size = parser["values"]["machine_nozzle_size"]

                    machine_extruder_count = '1' # by default it is 1 and the value cannot be stored in the global stack
                    if parser.has_option("values", "machine_extruder_count"):
                        machine_extruder_count = parser["values"]["machine_extruder_count"]

                    if machine_extruder_count == '1':
                        definition_name = parser["general"]["name"]
                        machine_extruders = self._getSingleExtrusionMachineExtruders(definition_name)

                        # For single extruder machine we need only first extruder
                        if len(machine_extruders) !=0:
                            self._updateSingleExtruderDefinitionFile(machine_extruders, machine_nozzle_size)
                            parser.remove_option("values", "machine_nozzle_size")

        # Update version numbers
        parser["metadata"]["setting_version"] = "5"


    def _getSingleExtrusionMachineExtruders(self, definition_name):

        machine_instances_dir = Resources.getPath(CuraApplication.ResourceTypes.MachineStack)

        machine_instance_id = None

        # Find machine instances
        for item in os.listdir(machine_instances_dir):
            file_path = os.path.join(machine_instances_dir, item)
            if not os.path.isfile(file_path):
                continue

            parser = configparser.ConfigParser(interpolation=None)
            try:
                parser.read([file_path])
            except:
                # skip, it is not a valid stack file
                continue

            if not parser.has_option("metadata", "type"):
                continue
            if "machine" != parser["metadata"]["type"]:
                continue

            if not parser.has_option("general", "id"):
                continue

            id = parser["general"]["id"]
            if id + "_settings" != definition_name:
                continue
            else:
                machine_instance_id = id
                break

        if machine_instance_id is not None:

            extruders_instances_dir = Resources.getPath(CuraApplication.ResourceTypes.ExtruderStack)
                        #"machine",[extruders]
            extruder_instances = []

            # Find all custom extruders for found machines
            for item in os.listdir(extruders_instances_dir):
                file_path = os.path.join(extruders_instances_dir, item)
                if not os.path.isfile(file_path):
                    continue

                parser = configparser.ConfigParser(interpolation=None)
                try:
                    parser.read([file_path])
                except:
                    # skip, it is not a valid stack file
                    continue

                if not parser.has_option("metadata", "type"):
                    continue
                if "extruder_train" != parser["metadata"]["type"]:
                    continue

                if not parser.has_option("metadata", "machine"):
                    continue
                if not parser.has_option("metadata", "position"):
                    continue

                if machine_instance_id != parser["metadata"]["machine"]:
                    continue

                extruder_instances.append(parser)

        return extruder_instances


    # Find extruder definition at index 0 and update its values
    def _updateSingleExtruderDefinitionFile(self, extruder_instances_per_machine, machine_nozzle_size):

        defintion_instances_dir = Resources.getPath(CuraApplication.ResourceTypes.DefinitionChangesContainer)

        for item in os.listdir(defintion_instances_dir):
            file_path = os.path.join(defintion_instances_dir, item)
            if not os.path.isfile(file_path):
                continue

            parser = configparser.ConfigParser(interpolation=None)
            try:
                parser.read([file_path])
            except:
                # skip, it is not a valid stack file
                continue

            if not parser.has_option("general", "name"):
                continue
            name = parser["general"]["name"]
            custom_extruder_at_0_position = None
            for extruder_instance in extruder_instances_per_machine:

                definition_position = extruder_instance["metadata"]["position"]

                if definition_position == "0":
                    custom_extruder_at_0_position = extruder_instance
                    break

            # If not null, then parsed file is for first extuder and then can be updated. I need to update only
            # first, because this update for single extuder machine
            if custom_extruder_at_0_position is not None:

                #Add new value
                parser["values"]["machine_nozzle_size"] = machine_nozzle_size

                definition_output = io.StringIO()
                parser.write(definition_output)

                with open(file_path, "w") as f:
                    f.write(definition_output.getvalue())

                return True

        return False


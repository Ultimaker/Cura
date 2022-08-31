# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import List, Tuple

from UM.VersionUpgrade import VersionUpgrade
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack
from cura.Machines.ContainerTree import ContainerTree
from cura.CuraApplication import CuraApplication
import io


class VersionUpgrade50to52(VersionUpgrade):
    """
    Upgrades configurations from the state they were in at version 5.0 to the
    state they should be in at version 5.2.
    """

    def upgradeMachine(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades container stacks to have the new version number.
        Upgrades container stacks for FLSun Racer to change their profiles.
        :param serialized: The original contents of the container stack.
        :param filename: The file name of the container stack.
        :return: A list of file names, and a list of the new contents for those files.
        """
        [filename], [serialized] = self.upgradeStack(serialized, filename)

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        connection_types = []
        if "metadata" in parser and "connection_type" in parser["metadata"]:
            connection_types = [int(connection_type) for connection_type in parser["metadata"]["connection_type"].split(",")]

        cloud_connection_types = ConnectionType.NetworkConnection, ConnectionType.CloudConnection

        if not any(connection_type in cloud_connection_types for connection_type in connection_types):
            return [filename], [serialized]

        stack = GlobalStack("")
        stack.deserialize(serialized)
        definition_id = stack.getDefinition().getId()

        abstract_machine_id = f"{definition_id}_abstract_machine"
        abstract_machine = GlobalStack(abstract_machine_id)
        abstract_machine.setMetaDataEntry("is_abstract_machine", True)
        abstract_machine.setMetaDataEntry("is_online", True)
        abstract_machine.setDefinition(stack.getDefinition())
        abstract_machine.setName(stack.getDefinition().getName())

        abstract_machine_filename = abstract_machine_id
        abstract_machine_serialized = abstract_machine.serialize()
        return [filename, abstract_machine_filename], [serialized, abstract_machine_serialized]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades container stacks to have the new version number.
        Upgrades container stacks for FLSun Racer to change their profiles.
        :param serialized: The original contents of the container stack.
        :param filename: The file name of the container stack.
        :return: A list of file names, and a list of the new contents for those files.
        """

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        parser["metadata"]["setting_version"] = "6000020"
        parser["general"]["version"] = "6"

        file = io.StringIO()
        parser.write(file)
        data = file.getvalue()

        return [filename], [data]


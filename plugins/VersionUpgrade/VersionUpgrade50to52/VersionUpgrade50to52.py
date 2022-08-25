# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import List, Tuple

from UM.VersionUpgrade import VersionUpgrade
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.CuraStackBuilder import CuraStackBuilder

class VersionUpgrade50to52(VersionUpgrade):
    """
    Upgrades configurations from the state they were in at version 5.0 to the
    state they should be in at version 5.2.
    """

    def upgradeStack(self, serialized: str, _filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades container stacks to have the new version number.
        Upgrades container stacks for FLSun Racer to change their profiles.
        :param serialized: The original contents of the container stack.
        :param filename: The file name of the container stack.
        :return: A list of file names, and a list of the new contents for those
        files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        connection_types = []
        if "metadata" in parser and "connection_type" in parser["metadata"]:
            connection_types = [int(connection_type) for connection_type in parser["metadata"]["connection_type"].split(",")]

        cloud_connection_types = ConnectionType.NetworkConnection, ConnectionType.CloudConnection

        if not any(connection_type in cloud_connection_types for connection_type in connection_types):
            return [], []

        definition_id = "ultimaker_s5"  # TODO use actual definition id from machine here
        abstract_machine = CuraStackBuilder.createAbstractMachine(definition_id)

        if abstract_machine:
            filename = f"{definition_id}_abstract_machine"
            data = abstract_machine.serialize()
            return [filename], [data]

        return [], []

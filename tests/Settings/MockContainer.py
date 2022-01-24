from typing import Optional

from UM.Settings.Interfaces import ContainerInterface
import UM.PluginObject
from UM.Signal import Signal


class MockContainer(ContainerInterface, UM.PluginObject.PluginObject):
    """Fake container class to add to the container registry.

    This allows us to test the container registry without testing the container
    class. If something is wrong in the container class it won't influence this
    test.
    """

    def __init__(self, metadata = None):
        """Initialise a new definition container.

        The container will have the specified ID and all metadata in the
        provided dictionary.
        """

        super().__init__()
        if metadata is None:
            self._metadata = {}
        else:
            self._metadata = metadata
        self._plugin_id = "MockContainerPlugin"

    def getId(self):
        """Gets the ID that was provided at initialisation.

        :return: The ID of the container.
        """

        return self._metadata["id"]

    def getMetaData(self):
        """Gets all metadata of this container.

        This returns the metadata dictionary that was provided in the
        constructor of this mock container.

        :return: The metadata for this container.
        """

        return self._metadata

    def getMetaDataEntry(self, entry, default = None):
        """Gets a metadata entry from the metadata dictionary.

        :param key: The key of the metadata entry.
        :return: The value of the metadata entry, or None if there is no such
        entry.
        """

        if entry in self._metadata:
            return self._metadata[entry]
        return default

    def getName(self):
        """Gets a human-readable name for this container.

        :return: The name from the metadata, or "MockContainer" if there was no
        name provided.
        """
        return self._metadata.get("name", "MockContainer")

    @property
    def isEnabled(self):
        """Get whether a container stack is enabled or not.

        :return: Always returns True.
        """
        return True

    def isReadOnly(self):
        """Get whether the container item is stored on a read only location in the filesystem.

        :return: Always returns False
        """

        return False

    def getPath(self):
        """Mock get path"""

        return "/path/to/the/light/side"

    def setPath(self, path):
        """Mock set path"""

        pass

    def getAllKeys(self):
        pass

    # Should return false (or even throw an exception) if trust (or other verification) is invalidated.
    def _trustHook(self, file_name: Optional[str]) -> bool:
        return True

    def setProperty(self, key, property_name, property_value, container = None, set_from_cache = False):
        pass

    def getProperty(self, key, property_name, context=None):
        if key in self.items:
            return self.items[key]

        return None

    def getValue(self, key):
        """Get the value of a container item.

        Since this mock container cannot contain any items, it always returns None.

        :return: Always returns None.
        """

        pass

    def hasProperty(self, key, property_name):
        """Get whether the container item has a specific property.

        This method is not implemented in the mock container.
        """

        return key in self.items

    def serialize(self, ignored_metadata_keys = None):
        """Serializes the container to a string representation.

        This method is not implemented in the mock container.
        """

        raise NotImplementedError()

    def deserialize(self, serialized, file_name: Optional[str] = None):
        """Deserializes the container from a string representation.

        This method is not implemented in the mock container.
        """

        raise NotImplementedError()

    @classmethod
    def getConfigurationTypeFromSerialized(cls, serialized: str):
        raise NotImplementedError()

    @classmethod
    def getVersionFromSerialized(cls, serialized):
        raise NotImplementedError()

    def isDirty(self):
        return True

    def setDirty(self, dirty):
        pass

    metaDataChanged = Signal()
    propertyChanged = Signal()
    containersChanged = Signal()

from unittest import TestCase
from unittest.mock import MagicMock

from cura.Settings.ContainerManager import ContainerManager


class TestContainerManager(TestCase):
    def setUp(self):

        self._application = MagicMock()
        self._container_registry = MagicMock()
        self._machine_manager = MagicMock()

        self._mocked_mime = MagicMock()
        self._mocked_mime.preferredSuffix = "omg"
        self._mocked_mime.comment = "UnitTest!"

        self._containers_meta_data = [{"id": "test", "test_data": "omg"}]
        self._container_registry.findContainersMetadata = MagicMock(return_value = self._containers_meta_data)
        self._container_registry.getMimeTypeForContainer = MagicMock(return_value = self._mocked_mime)

        self._application.getContainerRegistry = MagicMock(return_value = self._container_registry)
        self._application.getMachineManager = MagicMock(return_value = self._machine_manager)

        # Destroy the previous instance of the container manager
        if ContainerManager.getInstance() is not None:
            ContainerManager._ContainerManager__instance = None

        self._container_manager = ContainerManager(self._application)

    def test_getContainerMetaDataEntry(self):
        assert self._container_manager.getContainerMetaDataEntry("test", "test_data") == "omg"
        assert self._container_manager.getContainerMetaDataEntry("test", "entry_that_is_not_defined") == ""

    def test_clearUserContainer(self):
        self._container_manager.clearUserContainers()
        assert self._machine_manager.activeMachine.userChanges.clear.call_count == 1

    def test_getContainerNameFilters(self):
        # If nothing is added, we still expect to get the all files filter
        assert self._container_manager.getContainerNameFilters("") == ['All Files (*)']

        # Pretend that a new type was added.
        self._container_registry.getContainerTypes = MagicMock(return_value=[("None", None)])
        assert self._container_manager.getContainerNameFilters("") == ['UnitTest! (*.omg)', 'All Files (*)']

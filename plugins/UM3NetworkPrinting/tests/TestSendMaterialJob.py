# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import io
import json
from typing import Any, List
from unittest import TestCase, mock
from unittest.mock import patch, call

from PyQt5.QtCore import QByteArray

from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeType
from UM.Settings.ContainerRegistry import ContainerInterface, ContainerRegistryInterface, \
    DefinitionContainerInterface, ContainerRegistry
from plugins.UM3NetworkPrinting.src.ClusterUM3OutputDevice import ClusterUM3OutputDevice
from plugins.UM3NetworkPrinting.src.Models import ClusterMaterial
from plugins.UM3NetworkPrinting.src.SendMaterialJob import SendMaterialJob


class ContainerRegistryMock(ContainerRegistryInterface):

    def __init__(self):
        self.containersMetaData = None

    def findContainers(self, *, ignore_case: bool = False, **kwargs: Any) -> List[ContainerInterface]:
        raise NotImplementedError()

    def findDefinitionContainers(self, **kwargs: Any) -> List[DefinitionContainerInterface]:
        raise NotImplementedError()

    @classmethod
    def getApplication(cls) -> "Application":
        raise NotImplementedError()

    def getEmptyInstanceContainer(self) -> "InstanceContainer":
        raise NotImplementedError()

    def isReadOnly(self, container_id: str) -> bool:
        raise NotImplementedError()

    def setContainersMetadata(self, value):
        self.containersMetaData = value

    def findContainersMetadata(self, type):
        return self.containersMetaData


class FakeDevice(ClusterUM3OutputDevice):
    def _createFormPart(self, content_header, data, content_type=None):
        return "xxx"


class TestSendMaterialJob(TestCase):

    _LOCAL_MATERIAL_WHITE = {'type': 'material', 'status': 'unknown', 'id': 'generic_pla_white',
                            'base_file': 'generic_pla_white', 'setting_version': 5, 'name': 'White PLA',
                            'brand': 'Generic', 'material': 'PLA', 'color_name': 'White',
                            'GUID': 'badb0ee7-87c8-4f3f-9398-938587b67dce', 'version': '1', 'color_code': '#ffffff',
                            'description': 'Test PLA White', 'adhesion_info': 'Use glue.', 'approximate_diameter': '3',
                            'properties': {'density': '1.00', 'diameter': '2.85', 'weight': '750'},
                            'definition': 'fdmprinter', 'compatible': True}

    _LOCAL_MATERIAL_BLACK = {'type': 'material', 'status': 'unknown', 'id': 'generic_pla_black',
                            'base_file': 'generic_pla_black', 'setting_version': 5, 'name': 'Yellow CPE',
                            'brand': 'Ultimaker', 'material': 'CPE', 'color_name': 'Black',
                            'GUID': '5fbb362a-41f9-4818-bb43-15ea6df34aa4', 'version': '1', 'color_code': '#000000',
                            'description': 'Test PLA Black', 'adhesion_info': 'Use glue.', 'approximate_diameter': '3',
                            'properties': {'density': '1.01', 'diameter': '2.85', 'weight': '750'},
                            'definition': 'fdmprinter', 'compatible': True}

    _REMOTE_MATERIAL_WHITE = {
        "guid": "badb0ee7-87c8-4f3f-9398-938587b67dce",
        "material": "PLA",
        "brand": "Generic",
        "version": 1,
        "color": "White",
        "density": 1.00
    }

    _REMOTE_MATERIAL_BLACK = {
        "guid": "5fbb362a-41f9-4818-bb43-15ea6df34aa4",
        "material": "PLA",
        "brand": "Generic",
        "version": 2,
        "color": "Black",
        "density": 1.00
    }

    @patch("plugins.UM3NetworkPrinting.src.ClusterUM3OutputDevice")
    def test_run(self, device_mock):
        job = SendMaterialJob(device_mock)
        job.run()
        device_mock.get.assert_called_with("materials/", on_finished=job._onGetRemoteMaterials)

    @patch("plugins.UM3NetworkPrinting.src.ClusterUM3OutputDevice")
    @patch("PyQt5.QtNetwork.QNetworkReply")
    def test_sendMissingMaterials_withFailedRequest(self, reply_mock, device_mock):
        reply_mock.attribute.return_value = 404
        SendMaterialJob(device_mock).run()
        reply_mock.attribute.assert_called_with(0)
        self.assertEqual(reply_mock.method_calls, [call.attribute(0)])
        self.assertEqual(device_mock._onGetRemoteMaterials.method_calls, [])

    @patch("plugins.UM3NetworkPrinting.src.ClusterUM3OutputDevice")
    @patch("PyQt5.QtNetwork.QNetworkReply")
    def test_sendMissingMaterials_withBadJsonAnswer(self, reply_mock, device_mock):
        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(b'Six sick hicks nick six slick bricks with picks and sticks.')
        SendMaterialJob(device_mock).run()
        reply_mock.attribute.assert_called_with(0)
        self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.readAll()])
        self.assertEqual(device_mock._onGetRemoteMaterials.method_calls, [])

    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendMissingMaterials_withMissingGuid(self, reply_mock):
    #     reply_mock.attribute.return_value = 200
    #     remoteMaterialWithoutGuid = self._REMOTEMATERIAL_WHITE.copy()
    #     del remoteMaterialWithoutGuid["guid"]
    #     reply_mock.readAll.return_value = QByteArray(json.dumps([remoteMaterialWithoutGuid]).encode("ascii"))
    #
    #     with mock.patch.object(Logger, 'log', new=new_log):
    #         SendMaterialJob(None).sendMissingMaterials(reply_mock)
    #
    #     reply_mock.attribute.assert_called_with(0)
    #     self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.readAll()])
    #     self._assertLogEntries(
    #         [('e', "Request material storage on printer: Printer's answer was missing GUIDs.")],
    #         _logentries)
    #
    # @patch("UM.Resources.Resources.getAllResourcesOfType", lambda _: [])
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendMissingMaterials_WithInvalidVersionInLocalMaterial(self, reply_mock):
    #     reply_mock.attribute.return_value = 200
    #     reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTEMATERIAL_WHITE]).encode("ascii"))
    #
    #     containerRegistry = ContainerRegistryMock()
    #     localMaterialWhiteWithInvalidVersion = self._LOCALMATERIAL_WHITE.copy()
    #     localMaterialWhiteWithInvalidVersion["version"] = "one"
    #     containerRegistry.setContainersMetadata([localMaterialWhiteWithInvalidVersion])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             SendMaterialJob(None).sendMissingMaterials(reply_mock)
    #
    #     reply_mock.attribute.assert_called_with(0)
    #     self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.readAll()])
    #     self._assertLogEntries([('e', "Material generic_pla_white has invalid version number one.")], _logentries)
    #
    # @patch("UM.Resources.Resources.getAllResourcesOfType", lambda _: [])
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendMissingMaterials_WithMultipleLocalVersionsLowFirst(self, reply_mock):
    #     reply_mock.attribute.return_value = 200
    #     reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTEMATERIAL_WHITE]).encode("ascii"))
    #
    #     containerRegistry = ContainerRegistryMock()
    #     localMaterialWhiteWithHigherVersion = self._LOCALMATERIAL_WHITE.copy()
    #     localMaterialWhiteWithHigherVersion["version"] = "2"
    #     containerRegistry.setContainersMetadata([self._LOCALMATERIAL_WHITE, localMaterialWhiteWithHigherVersion])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             SendMaterialJob(None).sendMissingMaterials(reply_mock)
    #
    #     reply_mock.attribute.assert_called_with(0)
    #     self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.readAll()])
    #     self._assertLogEntries([], _logentries)
    #
    # @patch("UM.Resources.Resources.getAllResourcesOfType", lambda _: [])
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendMissingMaterials_MaterialMissingOnPrinter(self, reply_mock):
    #     reply_mock.attribute.return_value = 200
    #     reply_mock.readAll.return_value = QByteArray(
    #         json.dumps([self._REMOTEMATERIAL_WHITE]).encode("ascii"))
    #
    #     containerRegistry = ContainerRegistryMock()
    #     containerRegistry.setContainersMetadata([self._LOCALMATERIAL_WHITE, self._LOCALMATERIAL_BLACK])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             SendMaterialJob(None).sendMissingMaterials(reply_mock)
    #
    #     reply_mock.attribute.assert_called_with(0)
    #     self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.readAll()])
    #     self._assertLogEntries([], _logentries)
    #
    # @patch("builtins.open", lambda a, b: io.StringIO("<xml></xml>"))
    # @patch("UM.MimeTypeDatabase.MimeTypeDatabase.getMimeTypeForFile",
    #        lambda _: MimeType(name="application/x-ultimaker-material-profile", comment="Ultimaker Material Profile",
    #                           suffixes=["xml.fdm_material"]))
    # @patch("UM.Resources.Resources.getAllResourcesOfType", lambda _: ["/materials/generic_pla_white.xml.fdm_material"])
    # @patch("plugins.UM3NetworkPrinting.src.ClusterUM3OutputDevice")
    # def test_sendMaterialsToPrinter(self, device_mock):
    #     device_mock._createFormPart.return_value = "_xXx_"
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         job = SendMaterialJob(device_mock)
    #         job.sendMaterialsToPrinter({'generic_pla_white'})
    #
    #     self._assertLogEntries([("d", "Syncing material generic_pla_white with cluster.")], _logentries)
    #     self.assertEqual([call._createFormPart('name="file"; filename="generic_pla_white.xml.fdm_material"', '<xml></xml>'),
    #                       call.postFormWithParts(on_finished=job.sendingFinished, parts = ["_xXx_"], target = "materials/")], device_mock.method_calls)
    #
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendingFinished_success(self, reply_mock) -> None:
    #     reply_mock.attribute.return_value = 200
    #     with mock.patch.object(Logger, 'log', new=new_log):
    #         SendMaterialJob(None).sendingFinished(reply_mock)
    #
    #     reply_mock.attribute.assert_called_once_with(0)
    #     self.assertEqual(0, len(_logentries))
    #
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_sendingFinished_failed(self, reply_mock) -> None:
    #     reply_mock.attribute.return_value = 404
    #     reply_mock.readAll.return_value = QByteArray(b'Six sick hicks nick six slick bricks with picks and sticks.')
    #
    #     with mock.patch.object(Logger, 'log', new=new_log):
    #         SendMaterialJob(None).sendingFinished(reply_mock)
    #
    #     reply_mock.attribute.assert_called_with(0)
    #     self.assertEqual(reply_mock.method_calls, [call.attribute(0), call.attribute(0), call.readAll()])
    #
    #     self._assertLogEntries([
    #         ("e", "Received error code from printer when syncing material: 404"),
    #         ("e", "Six sick hicks nick six slick bricks with picks and sticks.")
    #     ], _logentries)
    #
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_parseReply(self, reply_mock):
    #     reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTEMATERIAL_WHITE]).encode("ascii"))
    #
    #     response = SendMaterialJob._parseReply(reply_mock)
    #
    #     self.assertTrue(len(response) == 1)
    #     self.assertEqual(next(iter(response.values())), ClusterMaterial(**self._REMOTEMATERIAL_WHITE))
    #
    # @patch("PyQt5.QtNetwork.QNetworkReply")
    # def test_parseReplyWithInvalidMaterial(self, reply_mock):
    #     remoteMaterialWithInvalidVersion = self._REMOTEMATERIAL_WHITE.copy()
    #     remoteMaterialWithInvalidVersion["version"] = "one"
    #     reply_mock.readAll.return_value = QByteArray(json.dumps([remoteMaterialWithInvalidVersion]).encode("ascii"))
    #
    #     with self.assertRaises(ValueError):
    #         SendMaterialJob._parseReply(reply_mock)
    #
    # def test__getLocalMaterials(self):
    #     containerRegistry = ContainerRegistryMock()
    #     containerRegistry.setContainersMetadata([self._LOCALMATERIAL_WHITE, self._LOCALMATERIAL_BLACK])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             local_materials = SendMaterialJob(None)._getLocalMaterials()
    #
    #     self.assertTrue(len(local_materials) == 2)
    #
    # def test__getLocalMaterialsWithMultipleVersions(self):
    #     containerRegistry = ContainerRegistryMock()
    #     localMaterialWithNewerVersion = self._LOCALMATERIAL_WHITE.copy()
    #     localMaterialWithNewerVersion["version"] = 2
    #     containerRegistry.setContainersMetadata([self._LOCALMATERIAL_WHITE, localMaterialWithNewerVersion])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             local_materials = SendMaterialJob(None)._getLocalMaterials()
    #
    #     self.assertTrue(len(local_materials) == 1)
    #     self.assertTrue(list(local_materials.values())[0].version == 2)
    #
    #     containerRegistry.setContainersMetadata([localMaterialWithNewerVersion, self._LOCALMATERIAL_WHITE])
    #
    #     with mock.patch.object(Logger, "log", new=new_log):
    #         with mock.patch.object(ContainerRegistry, "getInstance", lambda: containerRegistry):
    #             local_materials = SendMaterialJob(None)._getLocalMaterials()
    #
    #     self.assertTrue(len(local_materials) == 1)
    #     self.assertTrue(list(local_materials.values())[0].version == 2)
    #
    # def _assertLogEntries(self, first, second):
    #     """
    #     Inspects the two sets of log entry tuples and fails when they are not the same
    #     :param first: The first set of tuples
    #     :param second: The second set of tuples
    #     """
    #     self.assertEqual(len(first), len(second))
    #
    #     while len(first) > 0:
    #         e1, m1 = first[0]
    #         e2, m2 = second[0]
    #         self.assertEqual(e1, e2)
    #         self.assertEqual(m1, m2)
    #         first.pop(0)
    #         second.pop(0)

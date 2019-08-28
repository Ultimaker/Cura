# Copyright (c) 2019 Ultimaker B.V.
# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import io
import json
from unittest import TestCase, mock
from unittest.mock import patch, call, MagicMock

from PyQt5.QtCore import QByteArray

from UM.Application import Application

from cura.Machines.MaterialGroup import MaterialGroup
from cura.Machines.MaterialNode import MaterialNode

from ..src.SendMaterialJob import SendMaterialJob

_FILES_MAP = {"generic_pla_white": "/materials/generic_pla_white.xml.fdm_material",
              "generic_pla_black": "/materials/generic_pla_black.xml.fdm_material",
              }


@patch("builtins.open", lambda _, __: io.StringIO("<xml></xml>"))
class TestSendMaterialJob(TestCase):
    # version 1
    _LOCAL_MATERIAL_WHITE = {"type": "material", "status": "unknown", "id": "generic_pla_white",
                             "base_file": "generic_pla_white", "setting_version": "5", "name": "White PLA",
                             "brand": "Generic", "material": "PLA", "color_name": "White",
                             "GUID": "badb0ee7-87c8-4f3f-9398-938587b67dce", "version": "1", "color_code": "#ffffff",
                             "description": "Test PLA White", "adhesion_info": "Use glue.", "approximate_diameter": "3",
                             "properties": {"density": "1.00", "diameter": "2.85", "weight": "750"},
                             "definition": "fdmprinter", "compatible": True}

    # version 2
    _LOCAL_MATERIAL_WHITE_NEWER = {"type": "material", "status": "unknown", "id": "generic_pla_white",
                                   "base_file": "generic_pla_white", "setting_version": "5", "name": "White PLA",
                                   "brand": "Generic", "material": "PLA", "color_name": "White",
                                   "GUID": "badb0ee7-87c8-4f3f-9398-938587b67dce", "version": "2",
                                   "color_code": "#ffffff",
                                   "description": "Test PLA White", "adhesion_info": "Use glue.",
                                   "approximate_diameter": "3",
                                   "properties": {"density": "1.00", "diameter": "2.85", "weight": "750"},
                                   "definition": "fdmprinter", "compatible": True}

    # invalid version: "one"
    _LOCAL_MATERIAL_WHITE_INVALID_VERSION = {"type": "material", "status": "unknown", "id": "generic_pla_white",
                                             "base_file": "generic_pla_white", "setting_version": "5", "name": "White PLA",
                                             "brand": "Generic", "material": "PLA", "color_name": "White",
                                             "GUID": "badb0ee7-87c8-4f3f-9398-938587b67dce", "version": "one",
                                             "color_code": "#ffffff",
                                             "description": "Test PLA White", "adhesion_info": "Use glue.",
                                             "approximate_diameter": "3",
                                             "properties": {"density": "1.00", "diameter": "2.85", "weight": "750"},
                                             "definition": "fdmprinter", "compatible": True}

    _LOCAL_MATERIAL_WHITE_ALL_RESULT = {"generic_pla_white": MaterialGroup("generic_pla_white",
                                                                           MaterialNode(_LOCAL_MATERIAL_WHITE))}

    _LOCAL_MATERIAL_WHITE_NEWER_ALL_RESULT = {"generic_pla_white": MaterialGroup("generic_pla_white",
                                                                                 MaterialNode(_LOCAL_MATERIAL_WHITE_NEWER))}

    _LOCAL_MATERIAL_WHITE_INVALID_VERSION_ALL_RESULT = {"generic_pla_white": MaterialGroup("generic_pla_white",
                                                                                           MaterialNode(_LOCAL_MATERIAL_WHITE_INVALID_VERSION))}

    _LOCAL_MATERIAL_BLACK = {"type": "material", "status": "unknown", "id": "generic_pla_black",
                             "base_file": "generic_pla_black", "setting_version": "5", "name": "Yellow CPE",
                             "brand": "Ultimaker", "material": "CPE", "color_name": "Black",
                             "GUID": "5fbb362a-41f9-4818-bb43-15ea6df34aa4", "version": "1", "color_code": "#000000",
                             "description": "Test PLA Black", "adhesion_info": "Use glue.", "approximate_diameter": "3",
                             "properties": {"density": "1.01", "diameter": "2.85", "weight": "750"},
                             "definition": "fdmprinter", "compatible": True}

    _LOCAL_MATERIAL_BLACK_ALL_RESULT = {"generic_pla_black": MaterialGroup("generic_pla_black",
                                                                           MaterialNode(_LOCAL_MATERIAL_BLACK))}

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

    def test_run(self):
        device_mock = MagicMock()
        job = SendMaterialJob(device_mock)
        job.run()

        # We expect the materials endpoint to be called when the job runs.
        device_mock.get.assert_called_with("materials/", on_finished = job._onGetRemoteMaterials)

    def test__onGetRemoteMaterials_withFailedRequest(self):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        reply_mock.attribute.return_value = 404
        job = SendMaterialJob(device_mock)
        job._onGetRemoteMaterials(reply_mock)

        # We expect the device not to be called for any follow up.
        self.assertEqual(0, device_mock.createFormPart.call_count)

    def test__onGetRemoteMaterials_withWrongEncoding(self):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTE_MATERIAL_WHITE]).encode("cp500"))
        job = SendMaterialJob(device_mock)
        job._onGetRemoteMaterials(reply_mock)

        # Given that the parsing fails we do no expect the device to be called for any follow up.
        self.assertEqual(0, device_mock.createFormPart.call_count)

    def test__onGetRemoteMaterials_withBadJsonAnswer(self):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(b"Six sick hicks nick six slick bricks with picks and sticks.")
        job = SendMaterialJob(device_mock)
        job._onGetRemoteMaterials(reply_mock)

        # Given that the parsing fails we do no expect the device to be called for any follow up.
        self.assertEqual(0, device_mock.createFormPart.call_count)

    def test__onGetRemoteMaterials_withMissingGuidInRemoteMaterial(self):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        reply_mock.attribute.return_value = 200
        remote_material_without_guid = self._REMOTE_MATERIAL_WHITE.copy()
        del remote_material_without_guid["guid"]
        reply_mock.readAll.return_value = QByteArray(json.dumps([remote_material_without_guid]).encode("ascii"))
        job = SendMaterialJob(device_mock)
        job._onGetRemoteMaterials(reply_mock)

        # Given that parsing fails we do not expect the device to be called for any follow up.
        self.assertEqual(0, device_mock.createFormPart.call_count)

    @patch("cura.Machines.MaterialManager.MaterialManager")
    @patch("cura.Settings.CuraContainerRegistry")
    @patch("UM.Application")
    def test__onGetRemoteMaterials_withInvalidVersionInLocalMaterial(self, application_mock, container_registry_mock,
                                                                     material_manager_mock):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        application_mock.getContainerRegistry.return_value = container_registry_mock
        application_mock.getMaterialManager.return_value = material_manager_mock

        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTE_MATERIAL_WHITE]).encode("ascii"))

        material_manager_mock.getAllMaterialGroups.return_value = self._LOCAL_MATERIAL_WHITE_INVALID_VERSION_ALL_RESULT.copy()

        with mock.patch.object(Application, "getInstance", new = lambda: application_mock):
            job = SendMaterialJob(device_mock)
            job._onGetRemoteMaterials(reply_mock)

        self.assertEqual(0, device_mock.createFormPart.call_count)

    @patch("UM.Application.Application.getInstance")
    def test__onGetRemoteMaterials_withNoUpdate(self, application_mock):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        container_registry_mock = application_mock.getContainerRegistry.return_value
        material_manager_mock = application_mock.getMaterialManager.return_value

        device_mock.createFormPart.return_value = "_xXx_"

        material_manager_mock.getAllMaterialGroups.return_value = self._LOCAL_MATERIAL_WHITE_ALL_RESULT.copy()

        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTE_MATERIAL_WHITE]).encode("ascii"))

        with mock.patch.object(Application, "getInstance", new = lambda: application_mock):
            job = SendMaterialJob(device_mock)
            job._onGetRemoteMaterials(reply_mock)

        self.assertEqual(0, device_mock.createFormPart.call_count)
        self.assertEqual(0, device_mock.postFormWithParts.call_count)

    @patch("UM.Application.Application.getInstance")
    def test__onGetRemoteMaterials_withUpdatedMaterial(self, get_instance_mock):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        application_mock = get_instance_mock.return_value
        container_registry_mock = application_mock.getContainerRegistry.return_value
        material_manager_mock = application_mock.getMaterialManager.return_value

        container_registry_mock.getContainerFilePathById = lambda x: _FILES_MAP.get(x)

        device_mock.createFormPart.return_value = "_xXx_"

        material_manager_mock.getAllMaterialGroups.return_value = self._LOCAL_MATERIAL_WHITE_NEWER_ALL_RESULT.copy()

        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTE_MATERIAL_WHITE]).encode("ascii"))

        job = SendMaterialJob(device_mock)
        job._onGetRemoteMaterials(reply_mock)

        self.assertEqual(1, device_mock.createFormPart.call_count)
        self.assertEqual(1, device_mock.postFormWithParts.call_count)
        self.assertEqual(
            [call.createFormPart("name=\"file\"; filename=\"generic_pla_white.xml.fdm_material\"", "<xml></xml>"),
             call.postFormWithParts(target = "/materials/", parts = ["_xXx_"], on_finished = job.sendingFinished)],
            device_mock.method_calls)

    @patch("UM.Application.Application.getInstance")
    def test__onGetRemoteMaterials_withNewMaterial(self, application_mock):
        reply_mock = MagicMock()
        device_mock = MagicMock()
        container_registry_mock = application_mock.getContainerRegistry.return_value
        material_manager_mock = application_mock.getMaterialManager.return_value

        container_registry_mock.getContainerFilePathById = lambda x: _FILES_MAP.get(x)

        device_mock.createFormPart.return_value = "_xXx_"

        all_results = self._LOCAL_MATERIAL_WHITE_ALL_RESULT.copy()
        for key, value in self._LOCAL_MATERIAL_BLACK_ALL_RESULT.items():
            all_results[key] = value
        material_manager_mock.getAllMaterialGroups.return_value = all_results

        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = QByteArray(json.dumps([self._REMOTE_MATERIAL_BLACK]).encode("ascii"))

        with mock.patch.object(Application, "getInstance", new = lambda: application_mock):
            job = SendMaterialJob(device_mock)
            job._onGetRemoteMaterials(reply_mock)

        self.assertEqual(1, device_mock.createFormPart.call_count)
        self.assertEqual(1, device_mock.postFormWithParts.call_count)
        self.assertEqual(
            [call.createFormPart("name=\"file\"; filename=\"generic_pla_white.xml.fdm_material\"", "<xml></xml>"),
             call.postFormWithParts(target = "/materials/", parts = ["_xXx_"], on_finished = job.sendingFinished)],
            device_mock.method_calls)

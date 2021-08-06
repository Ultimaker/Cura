# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from itertools import product
from typing import List, Union, Dict, Optional, Any

from PyQt5.QtCore import QUrl

from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel

from .ClusterBuildPlate import ClusterBuildPlate
from .ClusterPrintCoreConfiguration import ClusterPrintCoreConfiguration
from .ClusterPrinterMaterialStation import ClusterPrinterMaterialStation
from .ClusterPrinterMaterialStationSlot import ClusterPrinterMaterialStationSlot
from .ClusterPrinterConfigurationMaterial import ClusterPrinterConfigurationMaterial
from ..BaseModel import BaseModel


class ClusterPrinterStatus(BaseModel):
    """Class representing a cluster printer"""


    def __init__(self, enabled: bool, firmware_version: str, friendly_name: str, ip_address: str, machine_variant: str,
                 status: str, unique_name: str, uuid: str,
                 configuration: List[Union[Dict[str, Any], ClusterPrintCoreConfiguration]],
                 reserved_by: Optional[str] = None, maintenance_required: Optional[bool] = None,
                 firmware_update_status: Optional[str] = None, latest_available_firmware: Optional[str] = None,
                 build_plate: Union[Dict[str, Any], ClusterBuildPlate] = None,
                 material_station: Union[Dict[str, Any], ClusterPrinterMaterialStation] = None, **kwargs) -> None:
        """Creates a new cluster printer status

        :param enabled: A printer can be disabled if it should not receive new jobs. By default every printer is enabled.
        :param firmware_version: Firmware version installed on the printer. Can differ for each printer in a cluster.
        :param friendly_name: Human readable name of the printer. Can be used for identification purposes.
        :param ip_address: The IP address of the printer in the local network.
        :param machine_variant: The type of printer. Can be 'Ultimaker 3' or 'Ultimaker 3ext'.
        :param status: The status of the printer.
        :param unique_name: The unique name of the printer in the network.
        :param uuid: The unique ID of the printer, also known as GUID.
        :param configuration: The active print core configurations of this printer.
        :param reserved_by: A printer can be claimed by a specific print job.
        :param maintenance_required: Indicates if maintenance is necessary.
        :param firmware_update_status: Whether the printer's firmware is up-to-date, value is one of: "up_to_date",
          "pending_update", "update_available", "update_in_progress", "update_failed", "update_impossible".
        :param latest_available_firmware: The version of the latest firmware that is available.
        :param build_plate: The build plate that is on the printer.
        :param material_station: The material station that is on the printer.
        """

        self.configuration = self.parseModels(ClusterPrintCoreConfiguration, configuration)
        self.enabled = enabled
        self.firmware_version = firmware_version
        self.friendly_name = friendly_name
        self.ip_address = ip_address
        self.machine_variant = machine_variant
        self.status = status
        self.unique_name = unique_name
        self.uuid = uuid
        self.reserved_by = reserved_by
        self.maintenance_required = maintenance_required
        self.firmware_update_status = firmware_update_status
        self.latest_available_firmware = latest_available_firmware
        self.build_plate = self.parseModel(ClusterBuildPlate, build_plate) if build_plate else None
        self.material_station = self.parseModel(ClusterPrinterMaterialStation,
                                                material_station) if material_station else None
        super().__init__(**kwargs)

    def createOutputModel(self, controller: PrinterOutputController) -> PrinterOutputModel:
        """Creates a new output model.

        :param controller: - The controller of the model.
        """
        model = PrinterOutputModel(controller, len(self.configuration), firmware_version = self.firmware_version)
        self.updateOutputModel(model)
        return model

    def updateOutputModel(self, model: PrinterOutputModel) -> None:
        """Updates the given output model.

        :param model: - The output model to update.
        """

        model.updateKey(self.uuid)
        model.updateName(self.friendly_name)
        model.updateUniqueName(self.unique_name)
        model.updateType(self.machine_variant)
        model.updateState(self.status if self.enabled else "disabled")
        model.updateBuildplate(self.build_plate.type if self.build_plate else "glass")
        model.setCameraUrl(QUrl("http://{}:8080/?action=stream".format(self.ip_address)))

        if not model.printerConfiguration:
            # Prevent accessing printer configuration when not available.
            # This sometimes happens when a printer was just added to a group and Cura is connected to that group.
            return

        # Set the possible configurations based on whether a Material Station is present or not.
        if self.material_station and self.material_station.material_slots:
            self._updateAvailableConfigurations(model)
        if self.configuration:
            self._updateActiveConfiguration(model)

    def _updateActiveConfiguration(self, model: PrinterOutputModel) -> None:
        configurations = zip(self.configuration, model.extruders, model.printerConfiguration.extruderConfigurations)
        for configuration, extruder_output, extruder_config in configurations:
            configuration.updateOutputModel(extruder_output)
            configuration.updateConfigurationModel(extruder_config)

    def _updateAvailableConfigurations(self, model: PrinterOutputModel) -> None:
        available_configurations = [self._createAvailableConfigurationFromPrinterConfiguration(
            left_slot = left_slot,
            right_slot = right_slot,
            printer_configuration = model.printerConfiguration
        ) for left_slot, right_slot in product(self._getSlotsForExtruder(0), self._getSlotsForExtruder(1))]
        model.setAvailableConfigurations(available_configurations)

    def _getSlotsForExtruder(self, extruder_index: int) -> List[ClusterPrinterMaterialStationSlot]:
        """Create a list of Material Station slots for the given extruder index.

        Returns a list with a single empty material slot if none are found to ensure we don't miss configurations.
        """

        if not self.material_station:  # typing guard
            return []
        slots = [slot for slot in self.material_station.material_slots if self._isSupportedConfiguration(
            slot = slot,
            extruder_index = extruder_index
        )]
        return slots or [self._createEmptyMaterialSlot(extruder_index)]

    @staticmethod
    def _isSupportedConfiguration(slot: ClusterPrinterMaterialStationSlot, extruder_index: int) -> bool:
        """Check if a configuration is supported in order to make it selectable by the user.

        We filter out any slot that is not supported by the extruder index, print core type or if the material is empty.
        """

        return slot.extruder_index == extruder_index and slot.compatible and not slot.material_empty

    @staticmethod
    def _createEmptyMaterialSlot(extruder_index: int) -> ClusterPrinterMaterialStationSlot:
        """Create an empty material slot with a fake empty material."""

        empty_material = ClusterPrinterConfigurationMaterial(guid = "", material = "empty", brand = "", color = "")
        return ClusterPrinterMaterialStationSlot(slot_index = 0, extruder_index = extruder_index,
                                                 compatible = True, material_remaining = 0, material = empty_material)

    @staticmethod
    def _createAvailableConfigurationFromPrinterConfiguration(left_slot: ClusterPrinterMaterialStationSlot,
                                                              right_slot: ClusterPrinterMaterialStationSlot,
                                                              printer_configuration: PrinterConfigurationModel
                                                              ) -> PrinterConfigurationModel:
        available_configuration = PrinterConfigurationModel()
        available_configuration.setExtruderConfigurations([left_slot.createConfigurationModel(),
                                                           right_slot.createConfigurationModel()])
        available_configuration.setPrinterType(printer_configuration.printerType)
        available_configuration.setBuildplateConfiguration(printer_configuration.buildplateConfiguration)
        return available_configuration

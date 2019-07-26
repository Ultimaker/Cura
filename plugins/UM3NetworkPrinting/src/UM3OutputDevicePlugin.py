# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Callable

from cura.CuraApplication import CuraApplication

from UM.OutputDevice.OutputDeviceManager import ManualDeviceAdditionAttempt
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from plugins.UM3NetworkPrinting.src.Network.NetworkOutputDeviceManager import NetworkOutputDeviceManager

from .Cloud.CloudOutputDeviceManager import CloudOutputDeviceManager


## This plugin handles the discovery and networking for Ultimaker 3D printers that support network and cloud printing.
class UM3OutputDevicePlugin(OutputDevicePlugin):

    # cloudFlowIsPossible = Signal()

    def __init__(self) -> None:
        super().__init__()

        # Create a network output device manager that abstracts all network connection logic away.
        self._network_output_device_manager = NetworkOutputDeviceManager()

        # Create a cloud output device manager that abstracts all cloud connection logic away.
        self._cloud_output_device_manager = CloudOutputDeviceManager()

        # Refresh network connections when another machine was selected in Cura.
        CuraApplication.getInstance().globalContainerStackChanged.connect(self.refreshConnections)

        # TODO: re-write cloud messaging
        # self._account = self._application.getCuraAPI().account

        # Check if cloud flow is possible when user logs in
        # self._account.loginStateChanged.connect(self.checkCloudFlowIsPossible)

        # Check if cloud flow is possible when user switches machines
        # self._application.globalContainerStackChanged.connect(self._onMachineSwitched)

        # Listen for when cloud flow is possible
        # self.cloudFlowIsPossible.connect(self._onCloudFlowPossible)

        # self._start_cloud_flow_message = None # type: Optional[Message]
        # self._cloud_flow_complete_message = None # type: Optional[Message]

        # self._cloud_output_device_manager.addedCloudCluster.connect(self._onCloudPrintingConfigured)
        # self._cloud_output_device_manager.removedCloudCluster.connect(self.checkCloudFlowIsPossible)

    ##  Start looking for devices in the network and cloud.
    def start(self):
        self._network_output_device_manager.start()
        self._cloud_output_device_manager.start()

    # Stop network and cloud discovery.
    def stop(self) -> None:
        self._network_output_device_manager.stop()
        self._cloud_output_device_manager.stop()

    ## Force refreshing the network connections.
    def refreshConnections(self) -> None:
        self._network_output_device_manager.refreshConnections()
        self._cloud_output_device_manager.refreshConnections()

    ## Indicate that this plugin supports adding networked printers manually.
    def canAddManualDevice(self, address: str = "") -> ManualDeviceAdditionAttempt:
        return ManualDeviceAdditionAttempt.POSSIBLE

    ## Add a networked printer manually based on its network address.
    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        self._network_output_device_manager.addManualDevice(address, callback)

    ## Remove a manually connected networked printer.
    def removeManualDevice(self, key: str, address: Optional[str] = None) -> None:
        self._network_output_device_manager.removeManualDevice(key, address)

    # ## Get the last manual device attempt.
    # #  Used by the DiscoverUM3Action.
    # def getLastManualDevice(self) -> str:
    #     return self._network_output_device_manager.getLastManualDevice()

    # ## Reset the last manual device attempt.
    # #  Used by the DiscoverUM3Action.
    # def resetLastManualDevice(self) -> None:
    #     self._network_output_device_manager.resetLastManualDevice()

    # ## Check if the prerequsites are in place to start the cloud flow
    # def checkCloudFlowIsPossible(self, cluster: Optional[CloudOutputDevice]) -> None:
    #     Logger.log("d", "Checking if cloud connection is possible...")
    #
    #     # Pre-Check: Skip if active machine already has been cloud connected or you said don't ask again
    #     active_machine = self._application.getMachineManager().activeMachine  # type: Optional[GlobalStack]
    #     if active_machine:
    #         # Check 1A: Printer isn't already configured for cloud
    #         if ConnectionType.CloudConnection.value in active_machine.configuredConnectionTypes:
    #             Logger.log("d", "Active machine was already configured for cloud.")
    #             return
    #
    #         # Check 1B: Printer isn't already configured for cloud
    #         if active_machine.getMetaDataEntry("cloud_flow_complete", False):
    #             Logger.log("d", "Active machine was already configured for cloud.")
    #             return
    #
    #         # Check 2: User did not already say "Don't ask me again"
    #         if active_machine.getMetaDataEntry("do_not_show_cloud_message", False):
    #             Logger.log("d", "Active machine shouldn't ask about cloud anymore.")
    #             return
    #
    #         # Check 3: User is logged in with an Ultimaker account
    #         if not self._account.isLoggedIn:
    #             Logger.log("d", "Cloud Flow not possible: User not logged in!")
    #             return
    #
    #         # Check 4: Machine is configured for network connectivity
    #         if not self._application.getMachineManager().activeMachineHasNetworkConnection:
    #             Logger.log("d", "Cloud Flow not possible: Machine is not connected!")
    #             return
    #
    #         # Check 5: Machine has correct firmware version
    #         firmware_version = self._application.getMachineManager().activeMachineFirmwareVersion # type: str
    #         if not Version(firmware_version) > self._min_cloud_version:
    #             Logger.log("d", "Cloud Flow not possible: Machine firmware (%s) is too low! (Requires version %s)",
    #                             firmware_version,
    #                             self._min_cloud_version)
    #             return
    #
    #         Logger.log("d", "Cloud flow is possible!")
    #         self.cloudFlowIsPossible.emit()

    # def _onCloudFlowPossible(self) -> None:
    #     # Cloud flow is possible, so show the message
    #     if not self._start_cloud_flow_message:
    #         self._createCloudFlowStartMessage()
    #     if self._start_cloud_flow_message and not self._start_cloud_flow_message.visible:
    #         self._start_cloud_flow_message.show()

    # def _onCloudPrintingConfigured(self, device) -> None:
    #     # Hide the cloud flow start message if it was hanging around already
    #     # For example: if the user already had the browser openen and made the association themselves
    #     if self._start_cloud_flow_message and self._start_cloud_flow_message.visible:
    #         self._start_cloud_flow_message.hide()
    #
    #     # Cloud flow is complete, so show the message
    #     if not self._cloud_flow_complete_message:
    #         self._createCloudFlowCompleteMessage()
    #     if self._cloud_flow_complete_message and not self._cloud_flow_complete_message.visible:
    #         self._cloud_flow_complete_message.show()
    #
    #     # Set the machine's cloud flow as complete so we don't ask the user again and again for cloud connected printers
    #     active_machine = self._application.getMachineManager().activeMachine
    #     if active_machine:
    #
    #         # The active machine _might_ not be the machine that was in the added cloud cluster and
    #         # then this will hide the cloud message for the wrong machine. So we only set it if the
    #         # host names match between the active machine and the newly added cluster
    #         saved_host_name = active_machine.getMetaDataEntry("um_network_key", "").split('.')[0]
    #         added_host_name = device.toDict()["host_name"]
    #
    #         if added_host_name == saved_host_name:
    #             active_machine.setMetaDataEntry("do_not_show_cloud_message", True)
    #
    #     return

    # def _onDontAskMeAgain(self, checked: bool) -> None:
    #     active_machine = self._application.getMachineManager().activeMachine # type: Optional[GlobalStack]
    #     if active_machine:
    #         active_machine.setMetaDataEntry("do_not_show_cloud_message", checked)
    #         if checked:
    #             Logger.log("d", "Will not ask the user again to cloud connect for current printer.")
    #     return

    # def _onCloudFlowStarted(self, messageId: str, actionId: str) -> None:
    #     address = self._application.getMachineManager().activeMachineAddress # type: str
    #     if address:
    #         QDesktopServices.openUrl(QUrl("http://" + address + "/cloud_connect"))
    #         if self._start_cloud_flow_message:
    #             self._start_cloud_flow_message.hide()
    #             self._start_cloud_flow_message = None
    #     return

    # def _onReviewCloudConnection(self, messageId: str, actionId: str) -> None:
    #     address = self._application.getMachineManager().activeMachineAddress # type: str
    #     if address:
    #         QDesktopServices.openUrl(QUrl("http://" + address + "/settings"))
    #     return

    # def _onMachineSwitched(self) -> None:
    #     # Hide any left over messages
    #     if self._start_cloud_flow_message is not None and self._start_cloud_flow_message.visible:
    #         self._start_cloud_flow_message.hide()
    #     if self._cloud_flow_complete_message is not None and self._cloud_flow_complete_message.visible:
    #         self._cloud_flow_complete_message.hide()
    #
    #     # Check for cloud flow again with newly selected machine
    #     self.checkCloudFlowIsPossible(None)

    # def _createCloudFlowStartMessage(self):
    #     self._start_cloud_flow_message = Message(
    #         text = i18n_catalog.i18nc("@info:status", "Send and monitor print jobs from anywhere using your Ultimaker account."),
    #         lifetime = 0,
    #         image_source = QUrl.fromLocalFile(os.path.join(
    #             PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting"),
    #             "resources", "svg", "cloud-flow-start.svg"
    #         )),
    #         image_caption = i18n_catalog.i18nc("@info:status Ultimaker Cloud is a brand name and shouldn't be translated.", "Connect to Ultimaker Cloud"),
    #         option_text = i18n_catalog.i18nc("@action", "Don't ask me again for this printer."),
    #         option_state = False
    #     )
    #     self._start_cloud_flow_message.addAction("", i18n_catalog.i18nc("@action", "Get started"), "", "")
    #     self._start_cloud_flow_message.optionToggled.connect(self._onDontAskMeAgain)
    #     self._start_cloud_flow_message.actionTriggered.connect(self._onCloudFlowStarted)

    # def _createCloudFlowCompleteMessage(self):
    #     self._cloud_flow_complete_message = Message(
    #         text = i18n_catalog.i18nc("@info:status", "You can now send and monitor print jobs from anywhere using your Ultimaker account."),
    #         lifetime = 30,
    #         image_source = QUrl.fromLocalFile(os.path.join(
    #             PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting"),
    #             "resources", "svg", "cloud-flow-completed.svg"
    #         )),
    #         image_caption = i18n_catalog.i18nc("@info:status", "Connected!")
    #     )
    #     self._cloud_flow_complete_message.addAction("", i18n_catalog.i18nc("@action", "Review your connection"), "", "", 1) # TODO: Icon
    #     self._cloud_flow_complete_message.actionTriggered.connect(self._onReviewCloudConnection)

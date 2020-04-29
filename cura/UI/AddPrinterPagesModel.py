# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .WelcomePagesModel import WelcomePagesModel


#
# This Qt ListModel is more or less the same the WelcomePagesModel, except that this model is only for adding a printer,
# so only the steps for adding a printer is included.
#
class AddPrinterPagesModel(WelcomePagesModel):

    def initialize(self) -> None:
        self._pages.append({"id": "add_network_or_local_printer",
                            "page_url": self._getBuiltinWelcomePagePath("AddNetworkOrLocalPrinterContent.qml"),
                            "next_page_id": "machine_actions",
                            "next_page_button_text": self._catalog.i18nc("@action:button", "Add"),
                            "previous_page_button_text": self._catalog.i18nc("@action:button", "Cancel"),
                            })
        self._pages.append({"id": "add_printer_by_ip",
                            "page_url": self._getBuiltinWelcomePagePath("AddPrinterByIpContent.qml"),
                            "next_page_id": "machine_actions",
                            })
        self._pages.append({"id": "add_cloud_printers",
                            "page_url": self._getBuiltinWelcomePagePath("AddCloudPrintersView.qml"),
                            "is_final_page": True,
                            "next_page_button_text": self._catalog.i18nc("@action:button", "Finish"),
                            })
        self._pages.append({"id": "machine_actions",
                            "page_url": self._getBuiltinWelcomePagePath("FirstStartMachineActionsContent.qml"),
                            "should_show_function": self.shouldShowMachineActions,
                            })
        self.setItems(self._pages)


__all__ = ["AddPrinterPagesModel"]

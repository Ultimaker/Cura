# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .WelcomePagesModel import WelcomePagesModel

from UM.Decorators import deprecated


#
# This Qt ListModel is more or less the same the WelcomePagesModel, except that this model is only for adding a printer,
# so only the steps for adding a printer is included.
#
class AddPrinterPagesModel(WelcomePagesModel):

    @deprecated("Argument 'cancellable' is unused and will be removed. It was actually effectless already since many versions.", since="5.14.0")
    def initialize(self, cancellable: bool = True) -> None:
        self._pages.append({"id": "add_network_or_local_printer",
                            "page_url": self._getBuiltinWelcomePagePath("AddUltimakerOrThirdPartyPrinterStack.qml"),
                            "next_page_id": "machine_actions",
                            "next_page_button_text": self._catalog.i18nc("@action:button", "Add"),
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

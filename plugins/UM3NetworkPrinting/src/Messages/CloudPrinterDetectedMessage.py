# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication

I18N_CATALOG = i18nCatalog("cura")


## Message shown when a new printer was added to your account but not yet in Cura.
class CloudPrinterDetectedMessage(Message):

    # Singleton used to prevent duplicate messages of this type at the same time.
    __is_visible = False

    # Store in preferences to hide this message in the future.
    _preference_key = "cloud/block_new_printers_popup"

    def __init__(self) -> None:
        super().__init__(
            title=I18N_CATALOG.i18nc("@info:title", "New cloud printers found"),
            text=I18N_CATALOG.i18nc("@info:message", "New printers have been found connected to your account, "
                                                     "you can find them in your list of discovered printers."),
            lifetime=0,
            dismissable=True,
            option_state=False,
            option_text=I18N_CATALOG.i18nc("@info:option_text", "Do not show this message again")
        )
        self.optionToggled.connect(self._onDontAskMeAgain)
        CuraApplication.getInstance().getPreferences().addPreference(self._preference_key, False)

    def show(self) -> None:
        if CuraApplication.getInstance().getPreferences().getValue(self._preference_key):
            return
        if CloudPrinterDetectedMessage.__is_visible:
            return
        super().show()
        CloudPrinterDetectedMessage.__is_visible = True

    def hide(self, send_signal = True) -> None:
        super().hide(send_signal)
        CloudPrinterDetectedMessage.__is_visible = False

    def _onDontAskMeAgain(self, checked: bool) -> None:
        CuraApplication.getInstance().getPreferences().setValue(self._preference_key, checked)

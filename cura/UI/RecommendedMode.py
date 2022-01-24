# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot

from cura import CuraApplication

#
# This object contains helper/convenience functions for Recommended mode.
#
class RecommendedMode(QObject):

    # Sets to use the adhesion or not for the "Adhesion" CheckBox in Recommended mode.
    @pyqtSlot(bool)
    def setAdhesion(self, checked: bool) -> None:
        application = CuraApplication.CuraApplication.getInstance()
        global_stack = application.getMachineManager().activeMachine
        if global_stack is None:
            return

        # Remove the adhesion type value set by the user.
        adhesion_type_key = "adhesion_type"
        user_changes_container = global_stack.userChanges
        if adhesion_type_key in user_changes_container.getAllKeys():
            user_changes_container.removeInstance(adhesion_type_key)

        # Get the default value of adhesion type after user's value has been removed.
        # skirt and none are counted as "no adhesion", the others are considered as "with adhesion". The conditions are
        # as the following:
        #  - if the user checks the adhesion checkbox, get the default value (including the custom quality) for adhesion
        #    type.
        #     (1) If the default value is "skirt" or "none" (no adhesion), set adhesion_type to "brim".
        #     (2) If the default value is "with adhesion", do nothing.
        #  - if the user unchecks the adhesion checkbox, get the default value (including the custom quality) for
        #    adhesion type.
        #     (1) If the default value is "skirt" or "none" (no adhesion), do nothing.
        #     (2) Otherwise, set adhesion_type to "skirt".
        value = global_stack.getProperty(adhesion_type_key, "value")
        if checked:
            if value in ("skirt", "none"):
                value = "brim"
        else:
            if value not in ("skirt", "none"):
                value = "skirt"

        user_changes_container.setProperty(adhesion_type_key, "value", value)


__all__ = ["RecommendedMode"]

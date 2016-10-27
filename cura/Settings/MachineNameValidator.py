# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import UM.Resources
import UM.Settings.ContainerRegistry
import UM.Settings.InstanceContainer

from PyQt5.QtGui import QValidator
import os #For statvfs.
import urllib #To escape machine names for how they're saved to file.

##  Are machine names valid?
#
#   Performs checks based on the length of the name.
class MachineNameValidator(QValidator):
    ##  Check if a specified machine name is allowed.
    #
    #   \param name The machine name to check.
    #   \param position The current position of the cursor in the text box.
    #   \return ``QValidator.Invalid`` if it's disallowed, or
    #   ``QValidator.Acceptable`` if it's allowed.
    def validate(self, name, position):
        #Check for file name length of the current settings container (which is the longest file we're saving with the name).
        try:
            filename_max_length = os.statvfs(UM.Resources.getDataStoragePath())
        except AttributeError: #Doesn't support statvfs. Probably because it's not a Unix system.
            filename_max_length = 255 #Assume it's Windows on NTFS.
        escaped_name = urllib.parse.quote_plus(name)
        current_settings_filename = escaped_name + "_current_settings." + UM.Settings.ContainerRegistry.getMimeTypeForContainer(UM.Settings.InstanceContainer).preferredSuffix
        if current_settings_filename > filename_max_length:
            return QValidator.Invalid

        return QValidator.Acceptable #All checks succeeded.
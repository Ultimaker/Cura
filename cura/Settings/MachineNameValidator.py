# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot, pyqtProperty, QObject, pyqtSignal, QRegExp
from PyQt5.QtGui import QValidator
import os #For statvfs.
import urllib #To escape machine names for how they're saved to file.

from UM.Resources import Resources
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer


class MachineNameValidator(QObject):
    """Are machine names valid?

    Performs checks based on the length of the name.
    """

    def __init__(self, parent = None):
        super().__init__(parent)

        #Compute the validation regex for printer names. This is limited by the maximum file name length.
        try:
            filename_max_length = os.statvfs(Resources.getDataStoragePath()).f_namemax
        except (AttributeError, EnvironmentError):  # Doesn't support statvfs. Probably because it's not a Unix system. Or perhaps there is no permission or it doesn't exist.
            filename_max_length = 255 #Assume it's Windows on NTFS.
        machine_name_max_length = filename_max_length - len("_current_settings.") - len(ContainerRegistry.getMimeTypeForContainer(InstanceContainer).preferredSuffix)
        # Characters that urllib.parse.quote_plus escapes count for 12! So now
        # we must devise a regex that allows only 12 normal characters or 1
        # special character, and that up to [machine_name_max_length / 12] times.
        maximum_special_characters = int(machine_name_max_length / 12)
        unescaped = r"[a-zA-Z0-9_\-\.\/]"
        self.machine_name_regex = r"^[^\.]((" + unescaped + "){0,12}|.){0," + str(maximum_special_characters) + r"}$"

    validationChanged = pyqtSignal()

    def validate(self, name):
        """Check if a specified machine name is allowed.

        :param name: The machine name to check.
        :return: ``QValidator.Invalid`` if it's disallowed, or ``QValidator.Acceptable`` if it's allowed.
        """

        #Check for file name length of the current settings container (which is the longest file we're saving with the name).
        try:
            filename_max_length = os.statvfs(Resources.getDataStoragePath()).f_namemax
        except AttributeError: #Doesn't support statvfs. Probably because it's not a Unix system.
            filename_max_length = 255 #Assume it's Windows on NTFS.
        escaped_name = urllib.parse.quote_plus(name)
        current_settings_filename = escaped_name + "_current_settings." + ContainerRegistry.getMimeTypeForContainer(InstanceContainer).preferredSuffix
        if len(current_settings_filename) > filename_max_length:
            return QValidator.Invalid

        return QValidator.Acceptable #All checks succeeded.

    @pyqtSlot(str)
    def updateValidation(self, new_name):
        """Updates the validation state of a machine name text field."""

        is_valid = self.validate(new_name)
        if is_valid == QValidator.Acceptable:
            self.validation_regex = "^.*$" #Matches anything.
        else:
            self.validation_regex = "a^" #Never matches (unless you manage to get "a" before the start of the string... good luck).
        self.validationChanged.emit()

    @pyqtProperty("QRegExp", notify=validationChanged)
    def machineNameRegex(self):
        return QRegExp(self.machine_name_regex)
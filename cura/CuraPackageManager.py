# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.CuraApplication import CuraApplication #To find some resource types.
from UM.PackageManager import PackageManager #The class we're extending.
from UM.Resources import Resources #To find storage paths for some resource types.


class CuraPackageManager(PackageManager):
    def __init__(self, application, parent = None):
        super().__init__(application, parent)

    def initialize(self):
        self._installation_dirs_dict["materials"] = Resources.getStoragePath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
        self._installation_dirs_dict["qualities"] = Resources.getStoragePath(CuraApplication.ResourceTypes.QualityInstanceContainer)

        super().initialize()

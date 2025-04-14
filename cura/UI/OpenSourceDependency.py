#  Copyright (c) 2025 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, pyqtProperty, pyqtEnum


class OpenSourceDependency(QObject):

    def __init__(self, name, data):
        super().__init__()
        self._name = name
        self._version = data['version'] if data['version'] is not None else ''
        self._summary = data['summary'] if data['summary'] is not None else ''
        self._license = data['license'] if data['license'] is not None and len(data['license']) > 0 else name
        self._license_full = data['license_full'] if 'license_full' in data else ''
        self._sources_url = data['sources_url'] if 'sources_url' in data else ''

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def version(self):
        return self._version

    @pyqtProperty(str, constant=True)
    def summary(self):
        return self._summary

    @pyqtProperty(str, constant=True)
    def license(self):
        return self._license

    @pyqtProperty(str, constant=True)
    def license_full(self):
        return self._license_full

    @pyqtProperty(str, constant=True)
    def sources_url(self):
        return self._sources_url
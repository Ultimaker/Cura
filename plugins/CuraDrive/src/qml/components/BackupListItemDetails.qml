// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ColumnLayout
{
    id: backupDetails
    width: parent.width
    spacing: UM.Theme.getSize("default_margin").width
    property var backupDetailsData

    // Cura version
    BackupListItemDetailsRow
    {
        iconSource: UM.Theme.getIcon("application")
        label: catalog.i18nc("@backuplist:label", "Cura Version")
        value: backupDetailsData.metadata.cura_release
    }

    // Machine count.
    BackupListItemDetailsRow
    {
        iconSource: UM.Theme.getIcon("printer_single")
        label: catalog.i18nc("@backuplist:label", "Machines")
        value: backupDetailsData.metadata.machine_count
    }

    // Material count
    BackupListItemDetailsRow
    {
        iconSource: UM.Theme.getIcon("category_material")
        label: catalog.i18nc("@backuplist:label", "Materials")
        value: backupDetailsData.metadata.material_count
    }

    // Profile count.
    BackupListItemDetailsRow
    {
        iconSource: UM.Theme.getIcon("settings")
        label: catalog.i18nc("@backuplist:label", "Profiles")
        value: backupDetailsData.metadata.profile_count
    }

    // Plugin count.
    BackupListItemDetailsRow
    {
        iconSource: UM.Theme.getIcon("plugin")
        label: catalog.i18nc("@backuplist:label", "Plugins")
        value: backupDetailsData.metadata.plugin_count
    }

    // Spacer.
    Item
    {
        width: parent.width
        height: UM.Theme.getSize("default_margin").height
    }
}

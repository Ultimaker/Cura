// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Tab
{
    id: base

    property string extruderId: "";
    property string quality: "";
    property string material: "";

    TableView
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width

        TableViewColumn { role: "label"; title: catalog.i18nc("@title:column", "Setting") }
        TableViewColumn { role: "profile_value"; title: catalog.i18nc("@title:column", "Profile Value"); }
        TableViewColumn { role: "user_value"; title: catalog.i18nc("@title:column", "User Value"); visible: quality == Cura.MachineManager.activeQualityId }
        TableViewColumn { role: "unit"; title: catalog.i18nc("@title:column", "Unit") }

        section.property: "category"
        section.delegate: Label { text: section }

        model: Cura.QualitySettingsModel
        {
            extruderId: base.extruderId != "" ? base.extruderId : null;
            quality: base.quality != null ? base.quality : "";
            material: base.material
        }
    }
}

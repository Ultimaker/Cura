// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

Rectangle
{
    property alias packageData: packageCardHeader.packageData
    property alias showUpdateButton:  packageCardHeader.showUpdateButton
    property alias showDisableButton:  packageCardHeader.showDisableButton
    property alias showInstallButton: packageCardHeader.showInstallButton

    height: childrenRect.height
    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width
    border.color: packageData.isMissingPackageInformation ? UM.Theme.getColor("warning") : "transparent"
    border.width: packageData.isMissingPackageInformation ? UM.Theme.getSize("default_lining").width : 0

    PackageCardHeader
    {
        id: packageCardHeader

        Item
        {
            id: shortDescription

            anchors.fill: parent

            UM.Label
            {
                id: descriptionLabel
                width: parent.width

                text: packageData.description
                maximumLineCount: 2
                elide: Text.ElideRight
                visible: text !== ""
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}

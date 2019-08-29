// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.1

import UM 1.3 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    // This dialog asks the user whether he/she wants to open a project file as a project or import models.
    id: base

    title: catalog.i18nc("@title:window", "Confirm uninstall") + toolbox.pluginToUninstall
    width: 450 * screenScaleFactor
    height: 50 * screenScaleFactor + dialogText.height + buttonBar.height

    maximumWidth: 450 * screenScaleFactor
    maximumHeight: 450 * screenScaleFactor
    minimumWidth: 450 * screenScaleFactor
    minimumHeight: 150 * screenScaleFactor

    modality: Qt.WindowModal

    Column
    {
        UM.I18nCatalog { id: catalog; name: "cura" }

        anchors
        {
            fill: parent
            leftMargin: Math.round(20 * screenScaleFactor)
            rightMargin: Math.round(20 * screenScaleFactor)
            topMargin: Math.round(10 * screenScaleFactor)
            bottomMargin: Math.round(10 * screenScaleFactor)
        }
        spacing: Math.round(15 * screenScaleFactor)

        Label
        {
            id: dialogText
            text:
            {
                var base_text = catalog.i18nc("@text:window", "You are uninstalling materials and/or profiles that are still in use. Confirming will reset the following materials/profiles to their defaults.")
                var materials_text = catalog.i18nc("@text:window", "Materials")
                var qualities_text = catalog.i18nc("@text:window", "Profiles")
                var machines_with_materials = toolbox.uninstallUsedMaterials
                var machines_with_qualities = toolbox.uninstallUsedQualities
                if (machines_with_materials != "")
                {
                    base_text += "\n\n" + materials_text +": \n" + machines_with_materials
                }
                if (machines_with_qualities != "")
                {
                    base_text += "\n\n" + qualities_text + ": \n" + machines_with_qualities
                }
                return base_text
            }
            anchors.left: parent.left
            anchors.right: parent.right
            font: UM.Theme.getFont("default")
            wrapMode: Text.WordWrap
            renderType: Text.NativeRendering
        }

        // Buttons
        Item {
            id: buttonBar
            anchors.right: parent.right
            anchors.left: parent.left
            height: childrenRect.height

            Button {
                id: cancelButton
                text: catalog.i18nc("@action:button", "Cancel")
                anchors.right: confirmButton.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                isDefault: true
                onClicked: toolbox.closeConfirmResetDialog()
            }

            Button {
                id: confirmButton
                text: catalog.i18nc("@action:button", "Confirm")
                anchors.right: parent.right
                onClicked: toolbox.resetMaterialsQualitiesAndUninstall()
            }
        }
    }
}

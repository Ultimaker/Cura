// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.9

import UM 1.5 as UM
import Cura 1.0 as Cura

// Dialog shown when the user closes Cura and there are unsaved workspace
// changes or an un-exported slice result.
UM.Dialog
{
    id: base
    readonly property UM.I18nCatalog catalog: UM.I18nCatalog { name: "cura" }

    title: catalog.i18nc("@title:window %1 is the application name", "Closing %1").arg(CuraApplication.applicationDisplayName)

    width: UM.Theme.getSize("small_popup_dialog").width
    height: UM.Theme.getSize("card").height
    minimumWidth: childrenRect.width + UM.Theme.getSize("default_margin").width * 2
    minimumHeight: childrenRect.height + UM.Theme.getSize("default_margin").height * 2
    maximumWidth: width
    maximumHeight: height

    backgroundColor: UM.Theme.getColor("main_background")
    modality: Qt.ApplicationModal

    property bool workspaceNotSaved: false
    property bool sliceNotExported: false
    property bool isSlicing: false

    UM.Label
    {
        id: mainText
        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }
        wrapMode: Text.WordWrap
        text:
        {
            var parts = []
            if (base.isSlicing)
            {
                parts.push(catalog.i18nc("@label", "A slice operation is in progress. Closing will abort it."))
            }
            if (base.workspaceNotSaved)
            {
                parts.push(catalog.i18nc("@label", "You have unsaved changes to the project."))
            }
            if (base.sliceNotExported)
            {
                parts.push(catalog.i18nc("@label", "The slice result has not been exported."))
            }
            parts.push(catalog.i18nc(
                "@label %1 is the application name",
                "What would you like to do before %1 closes?"
            ).arg(CuraApplication.applicationDisplayName))
            return parts.join(" ")
        }
    }

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    rightButtons:
    [
        Cura.SecondaryButton
        {
            id: cancelButton
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked:
            {
                base.hide()
                CuraApplication.cancelExitFromSafeWorkspace()
            }
        },
        Cura.SecondaryButton
        {
            id: discardButton
            text: catalog.i18nc("@action:button", "Discard & Close")
            onClicked:
            {
                base.hide()
                CuraApplication.discardAndCloseFromSafeWorkspace()
            }
        },
        Cura.PrimaryButton
        {
            id: saveProjectButton
            visible: base.workspaceNotSaved
            text: catalog.i18nc("@action:button", "Save Project")
            onClicked:
            {
                base.hide()
                CuraApplication.saveProjectFromSafeWorkspace()
            }
        },
        Cura.PrimaryButton
        {
            id: exportSliceButton
            visible: base.sliceNotExported && !base.isSlicing
            text: catalog.i18nc("@action:button", "Export Slice Result")
            onClicked:
            {
                base.hide()
                CuraApplication.exportSliceFromSafeWorkspace()
            }
        }
    ]
}


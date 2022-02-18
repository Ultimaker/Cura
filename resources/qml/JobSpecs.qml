// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    property bool activity: CuraApplication.platformActivity
    property string fileBaseName: (PrintInformation === null) ? "" : PrintInformation.baseName

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    width: childrenRect.width
    height: childrenRect.height

    onActivityChanged:
    {
        if (!activity)
        {
            // When there is no mesh in the buildplate; the printJobTextField is set to an empty string so it doesn't
            // set an empty string as a jobName (which is later used for saving the file)
            PrintInformation.baseName = ""
        }
    }

    Item
    {
        id: jobNameRow
        anchors.top: parent.top
        anchors.left: parent.left
        height: UM.Theme.getSize("jobspecs_line").height

        UM.SimpleButton
        {
            id: printJobPencilIcon
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("save_button_specs_icons").width
            height: UM.Theme.getSize("save_button_specs_icons").height
            iconSource: UM.Theme.getIcon("Pen")
            hoverColor: UM.Theme.getColor("small_button_text_hover")
            color:  UM.Theme.getColor("small_button_text")
            onClicked:
            {
                printJobTextfield.selectAll()
                printJobTextfield.focus = true
            }
        }

        TextField
        {
            id: printJobTextfield
            anchors.left: printJobPencilIcon.right
            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
            height: UM.Theme.getSize("jobspecs_line").height
            width: Math.max(contentWidth + UM.Theme.getSize("default_margin").width, 50)
            maximumLength: 120
            text: PrintInformation === null ? "" : PrintInformation.jobName
            horizontalAlignment: TextInput.AlignLeft

            property string textBeforeEdit: ""

            onActiveFocusChanged:
            {
                if (activeFocus)
                {
                    textBeforeEdit = text
                }
            }

            onEditingFinished:
            {
                if (text != textBeforeEdit) {
                    var new_name = text == "" ? catalog.i18nc("@text Print job name", "Untitled") : text
                    PrintInformation.setJobName(new_name, true)
                }
                printJobTextfield.focus = false
            }

            validator: RegExpValidator {
                regExp: /^[^\\\/\*\?\|\[\]]*$/
            }
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_scene")
            background: Item {}
            selectByMouse: true
        }
    }

    UM.Label
    {
        id: boundingSpec
        anchors.top: jobNameRow.bottom
        anchors.left: parent.left

        height: UM.Theme.getSize("jobspecs_line").height
        color: UM.Theme.getColor("text_scene")
        text: CuraApplication.getSceneBoundingBoxString
    }

    Row
    {
        id: additionalComponentsRow
        anchors.top: boundingSpec.top
        anchors.bottom: boundingSpec.bottom
        anchors.left: boundingSpec.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
    }

    Component.onCompleted: base.addAdditionalComponents("jobSpecsButton")

    Connections
    {
        target: CuraApplication
        function onAdditionalComponentsChanged(areaId) { base.addAdditionalComponents("jobSpecsButton") }
    }

    function addAdditionalComponents(areaId)
    {
        if (areaId == "jobSpecsButton")
        {
            for (var component in CuraApplication.additionalComponents["jobSpecsButton"])
            {
                CuraApplication.additionalComponents["jobSpecsButton"][component].parent = additionalComponentsRow
            }
        }
    }
}

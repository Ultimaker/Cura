// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import "Menus" // TODO: This needs to be fixed in the qmldir!

Rectangle
{
    implicitWidth: parent.width
    implicitHeight: parent.height

    id: base
    color: UM.Theme.getColor("sidebar")

    // Height has an extra 2x margin for the top & bottom margin.
    height: childrenRect.height + 2 * UM.Theme.getSize("default_margin").width

    Cura.ExtrudersModel { id: extrudersModel }

    ListView
    {
        // Horizontal list that shows the extruders
        id: extrudersList
        visible: extrudersModel.items.length > 1
        property var index: 0

        height: UM.Theme.getSize("sidebar_header_mode_tabs").height
        boundsBehavior: Flickable.StopAtBounds

        anchors
        {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: UM.Theme.getSize("sidebar_margin").width
        }

        ExclusiveGroup { id: extruderMenuGroup }

        orientation: ListView.Horizontal

        model: extrudersModel

        Connections
        {
            target: Cura.MachineManager
            onGlobalContainerChanged: forceActiveFocus() // Changing focus applies the currently-being-typed values so it can change the displayed setting values.
        }

        delegate: Button
        {
            height: parent.height
            width: Math.round(ListView.view.width / extrudersModel.rowCount())

            text: model.name
            tooltip: model.name
            exclusiveGroup: extruderMenuGroup
            checked: Cura.ExtruderManager.activeExtruderIndex == index

            property bool extruder_enabled: true

            MouseArea // TODO; This really should be fixed. It makes absolutely no sense to have a button AND a mouse area.
            {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked:
                {
                    switch (mouse.button)
                    {
                        case Qt.LeftButton:
                            extruder_enabled = Cura.MachineManager.getExtruder(model.index).isEnabled
                            if (extruder_enabled)
                            {
                                forceActiveFocus(); // Changing focus applies the currently-being-typed values so it can change the displayed setting values.
                                Cura.ExtruderManager.setActiveExtruderIndex(index);
                            }
                            break;
                        case Qt.RightButton:
                            extruder_enabled = Cura.MachineManager.getExtruder(model.index).isEnabled
                            extruderMenu.popup();
                            break;
                    }

                }
            }

            Menu
            {
                id: extruderMenu

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu", "Enable Extruder")
                    onTriggered: Cura.MachineManager.setExtruderEnabled(model.index, true)
                    visible: !extruder_enabled  // using an intermediate variable prevents an empty popup that occured now and then
                }

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu", "Disable Extruder")
                    onTriggered: Cura.MachineManager.setExtruderEnabled(model.index, false)
                    visible: extruder_enabled
                    enabled: Cura.MachineManager.numberExtrudersEnabled > 1
                }
            }

            style: ButtonStyle
            {
                background: Rectangle
                {
                    anchors.fill: parent
                    border.width: control.checked ? UM.Theme.getSize("default_lining").width * 2 : UM.Theme.getSize("default_lining").width
                    border.color:
                    {
                        if (Cura.MachineManager.getExtruder(index).isEnabled)
                        {
                            if(control.checked || control.pressed)
                            {
                                return  UM.Theme.getColor("action_button_active_border");
                            } else if (control.hovered)
                            {
                                return UM.Theme.getColor("action_button_hovered_border")
                            }
                            return UM.Theme.getColor("action_button_border")
                        }
                        return UM.Theme.getColor("action_button_disabled_border")
                    }
                    color:
                    {
                        if (Cura.MachineManager.getExtruder(index).isEnabled)
                        {
                            if(control.checked || control.pressed)
                            {
                                return  UM.Theme.getColor("action_button_active");
                            }
                            else if (control.hovered)
                            {
                                return UM.Theme.getColor("action_button_hovered")
                            }
                            return UM.Theme.getColor("action_button")
                        }
                        return UM.Theme.getColor("action_button_disabled")
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }

                    Item
                    {
                        id: extruderButtonFace
                        anchors.centerIn: parent
                        width: childrenRect.width

                        Label
                        {
                            // Static text that holds the "Extruder" label
                            id: extruderStaticText
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left

                            color:
                            {
                                if (Cura.MachineManager.getExtruder(index).isEnabled)
                                {
                                    if(control.checked || control.pressed)
                                    {
                                        return  UM.Theme.getColor("action_button_active_text");
                                    }
                                    else if (control.hovered)
                                    {
                                        return UM.Theme.getColor("action_button_hovered_text")
                                    }
                                    return UM.Theme.getColor("action_button_text")
                                }
                                return UM.Theme.getColor("action_button_disabled_text")
                            }

                            font: UM.Theme.getFont("large_nonbold")
                            text: catalog.i18nc("@label", "Extruder")
                            visible: width < (control.width - extruderIcon.width - UM.Theme.getSize("default_margin").width)
                            elide: Text.ElideRight
                        }

                        ExtruderIcon
                        {
                            // Round icon with the extruder number and material color indicator.
                            id: extruderIcon

                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: extruderStaticText.right
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width
                            width: control.height - Math.round(UM.Theme.getSize("default_margin").width / 2)
                            height: width

                            checked: control.checked
                            material_color: model.color
                            text_color: extruderStaticText.color
                        }
                    }
                }

                label: Item {}
            }
        }
    }

    Item
    {
        id: materialRow
        height: UM.Theme.getSize("sidebar_setup").height
        visible: Cura.MachineManager.hasMaterials

        anchors
        {
            left: parent.left
            right: parent.right
            top: extrudersList.bottom
            margins: UM.Theme.getSize("sidebar_margin").width
        }

        Label
        {
            id: materialLabel
            text: catalog.i18nc("@label", "Material");
            width: Math.round(parent.width * 0.45 - UM.Theme.getSize("default_margin").width)
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton
        {
            id: materialSelection

            property var activeExtruder: Cura.MachineManager.activeStack
            property var hasActiveExtruder: activeExtruder != null
            property var currentRootMaterialName: hasActiveExtruder ? activeExtruder.material.name : ""

            text: currentRootMaterialName
            tooltip: currentRootMaterialName
            visible: Cura.MachineManager.hasMaterials

            enabled: !extrudersList.visible || Cura.ExtruderManager.activeExtruderIndex > -1

            height: UM.Theme.getSize("setting_control").height
            width: Math.round(parent.width * 0.7) + UM.Theme.getSize("sidebar_margin").width
            anchors.right: parent.right
            style: UM.Theme.styles.sidebar_header_button
            activeFocusOnPress: true;
            menu: MaterialMenu
            {
                extruderIndex: Cura.ExtruderManager.activeExtruderIndex
            }

            property var valueError: hasActiveExtruder ? Cura.ContainerManager.getContainerMetaDataEntry(activeExtruder.material.id, "compatible", "") != "True" : true
            property var valueWarning: ! Cura.MachineManager.isActiveQualitySupported
        }
    }

    Item
    {
        id: variantRow
        height: UM.Theme.getSize("sidebar_setup").height
        visible: Cura.MachineManager.hasVariants

        anchors
        {
            left: parent.left
            right: parent.right
            top: materialRow.bottom
            margins: UM.Theme.getSize("sidebar_margin").width
        }

        Label
        {
            id: variantLabel
            text: Cura.MachineManager.activeDefinitionVariantsName;
            width: Math.round(parent.width * 0.45 - UM.Theme.getSize("default_margin").width)
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton
        {
            id: variantSelection
            text: Cura.MachineManager.activeVariantName
            tooltip: Cura.MachineManager.activeVariantName;
            visible: Cura.MachineManager.hasVariants

            height: UM.Theme.getSize("setting_control").height
            width: Math.round(parent.width * 0.7 + UM.Theme.getSize("sidebar_margin").width)
            anchors.right: parent.right
            style: UM.Theme.styles.sidebar_header_button
            activeFocusOnPress: true;

            menu: NozzleMenu { extruderIndex: Cura.ExtruderManager.activeExtruderIndex }
        }
    }

    Item
    {
        id: materialCompatibilityLink
        height: UM.Theme.getSize("sidebar_setup").height

        anchors.right: parent.right
        anchors.top: variantRow.bottom
        anchors.margins: UM.Theme.getSize("sidebar_margin").width
        UM.RecolorImage
        {
            id: warningImage

            anchors.right: materialInfoLabel.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width

            source: UM.Theme.getIcon("warning")
            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height

            sourceSize.width: width
            sourceSize.height: height

            color: UM.Theme.getColor("material_compatibility_warning")

            visible: !Cura.MachineManager.isCurrentSetupSupported
        }

        Label
        {
            id: materialInfoLabel
            wrapMode: Text.WordWrap
            text: "<a href='%1'>" + catalog.i18nc("@label", "Check compatibility") + "</a>"
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            linkColor: UM.Theme.getColor("text_link")

            verticalAlignment: Text.AlignTop

            anchors.right: parent.right

            MouseArea
            {
                anchors.fill: parent

                onClicked: {
                    // open the material URL with web browser
                    Qt.openUrlExternally("https://ultimaker.com/incoming-links/cura/material-compatibilty");
                }
            }
        }
    }

}

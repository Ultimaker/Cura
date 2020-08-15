// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Button
{
    id: objectItemButton

    width: parent.width
    height: UM.Theme.getSize("action_button").height
    leftPadding: UM.Theme.getSize("thin_margin").width
    rightPadding: perObjectSettingsInfo.visible ? UM.Theme.getSize("default_lining").width : UM.Theme.getSize("thin_margin").width
    checkable: true
    hoverEnabled: true

    onClicked: Cura.SceneController.changeSelection(index)

    background: Rectangle
    {
        id: backgroundRect
        color: objectItemButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: objectItemButton.checked ? UM.Theme.getColor("primary") : "transparent"
    }

    contentItem: Item
    {
        width: objectItemButton.width - objectItemButton.leftPadding
        height: UM.Theme.getSize("action_button").height

        UM.RecolorImage
        {
            id: swatch
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            width: height
            height: parent.height - UM.Theme.getSize("narrow_margin").height
            source: UM.Theme.getIcon("extruder_button")
            color: extruderColor
            visible: showExtruderSwatches && extruderColor != ""
        }

        Label
        {
            id: buttonText
            anchors
            {
                left: showExtruderSwatches ? swatch.right : parent.left
                leftMargin: showExtruderSwatches ? UM.Theme.getSize("narrow_margin").width : 0
                right: perObjectSettingsInfo.visible ? perObjectSettingsInfo.left : parent.right
                verticalCenter: parent.verticalCenter
            }
            text: objectItemButton.text
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text_scene")
            opacity: (outsideBuildArea) ? 0.5 : 1.0
            visible: text != ""
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        Button
        {
            id: perObjectSettingsInfo

            anchors
            {
                right: parent.right
                rightMargin: 0
            }
            width: childrenRect.width
            height: parent.height
            padding: 0
            leftPadding: UM.Theme.getSize("thin_margin").width
            visible: meshType != "" || perObjectSettingsCount > 0

            onClicked:
            {
                Cura.SceneController.changeSelection(index)
                UM.Controller.setActiveTool("PerObjectSettingsTool")
            }

            property string tooltipText:
            {
                var result = "";
                if (!visible)
                {
                    return result;
                }
                if (meshType != "")
                {
                    result += "<br>";
                    switch (meshType) {
                        case "support_mesh":
                            result += catalog.i18nc("@label", "Is printed as support.");
                            break;
                        case "cutting_mesh":
                            result += catalog.i18nc("@label", "Other models overlapping with this model are modified.");
                            break;
                        case "infill_mesh":
                            result += catalog.i18nc("@label", "Infill overlapping with this model is modified.");
                            break;
                        case "anti_overhang_mesh":
                            result += catalog.i18nc("@label", "Overlaps with this model are not supported.");
                            break;
                    }
                }
                if (perObjectSettingsCount != "")
                {
                    result += "<br>" + catalog.i18ncp(
                        "@label", "Overrides %1 setting.", "Overrides %1 settings.", perObjectSettingsCount
                    ).arg(perObjectSettingsCount);
                }
                return result;
            }

            contentItem: Item
            {
                height: parent.height
                width: meshTypeIcon.width + perObjectSettingsCountLabel.width + UM.Theme.getSize("narrow_margin").width

                Cura.NotificationIcon
                {
                    id: perObjectSettingsCountLabel
                    anchors
                    {
                        right: parent.right
                        rightMargin: 0
                    }
                    visible: perObjectSettingsCount > 0
                    color: UM.Theme.getColor("text_scene")
                    labelText: perObjectSettingsCount.toString()
                }

                UM.RecolorImage
                {
                    id: meshTypeIcon
                    anchors
                    {
                        right: perObjectSettingsCountLabel.left
                        rightMargin: UM.Theme.getSize("narrow_margin").width
                    }

                    width: parent.height
                    height: parent.height
                    color: UM.Theme.getColor("text_scene")
                    visible: meshType != ""
                    source:
                    {
                        switch (meshType) {
                            case "support_mesh":
                                return UM.Theme.getIcon("pos_print_as_support");
                            case "cutting_mesh":
                            case "infill_mesh":
                                return UM.Theme.getIcon("pos_modify_overlaps");
                            case "anti_overhang_mesh":
                                return UM.Theme.getIcon("pos_modify_dont_support_overlap");
                        }
                        return "";
                    }
                }
            }

            background: Item {}
        }
    }

    TextMetrics
    {
        id: buttonTextMetrics
        text: buttonText.text
        font: buttonText.font
        elide: buttonText.elide
        elideWidth: buttonText.width
    }

    Cura.ToolTip
    {
        id: tooltip
        tooltipText: objectItemButton.text + perObjectSettingsInfo.tooltipText
        visible: objectItemButton.hovered && (buttonTextMetrics.elidedText != buttonText.text || perObjectSettingsInfo.visible)
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }
}

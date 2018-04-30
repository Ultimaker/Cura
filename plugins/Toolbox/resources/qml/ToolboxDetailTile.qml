// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: tile
    property bool installed: toolbox.isInstalled(model.id)
    width: detailList.width - UM.Theme.getSize("wide_margin").width
    // TODO: Without this line, every instance of this object has 0 height. With
    // it, QML spits out tons of bugs claiming a binding loop (not true). Why?
    // Because QT is garbage.
    height: Math.max( UM.Theme.getSize("toolbox_detail_tile").height, childrenRect.height + UM.Theme.getSize("default_margin").height)
    Item
    {
        id: normalData
        height: childrenRect.height
        anchors
        {
            left: parent.left
            right: controls.left
            rightMargin: UM.Theme.getSize("default_margin").width
            top: parent.top
        }
        Label
        {
            id: packageName
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
            text: model.name
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium_bold")
        }
        Label
        {
            anchors.top: packageName.bottom
            width: parent.width
            text:
            {
                if (model.description.length > 235)
                {
                    if (model.description.substring(234, 235) == " ")
                    {
                        return model.description.substring(0, 234) + "..."
                    }
                    else
                    {
                        return model.description.substring(0, 235) + "..."
                    }
                }
                return model.description
            }
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
        }
    }
    Item
    {
        id: controls
        anchors.right: tile.right
        anchors.top: tile.top
        width: childrenRect.width
        height: childrenRect.height
        Button
        {
            id: installButton
            text:
            {
                if (installed)
                {
                    return catalog.i18nc("@action:button", "Installed")
                }
                else
                {
                    if ( toolbox.isDownloading && toolbox.activePackage == model )
                    {
                        return catalog.i18nc("@action:button", "Cancel")
                    }
                    else
                    {
                        return catalog.i18nc("@action:button", "Install")
                    }
                }
            }
            enabled:
            {
                if (installed)
                {
                    return true
                }
                if ( toolbox.isDownloading )
                {
                    return toolbox.activePackage == model ? true : false
                }
                else
                {
                    return true
                }
            }
            opacity: enabled ? 1.0 : 0.5
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: 96
                    implicitHeight: 30
                    color:
                    {
                        if (installed)
                        {
                            return UM.Theme.getColor("action_button_disabled")
                        }
                        else
                        {
                            if ( control.hovered )
                            {
                                return UM.Theme.getColor("primary_hover")
                            }
                            else
                            {
                                return UM.Theme.getColor("primary")
                            }
                        }

                    }
                }
                label: Label
                {
                    text: control.text
                    color:
                    {
                        if (installed)
                        {
                            return UM.Theme.getColor("action_button_disabled_text")
                        }
                        else
                        {
                            if ( control.hovered )
                            {
                                return UM.Theme.getColor("button_text_hover")
                            }
                            else
                            {
                                return UM.Theme.getColor("button_text")
                            }
                        }
                    }
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font: UM.Theme.getFont("default_bold")
                }
            }
            onClicked:
            {
                if (installed)
                {
                    toolbox.viewCategory = "installed"
                }
                else
                {
                    // if ( toolbox.isDownloading && toolbox.activePackage == model )
                    if ( toolbox.isDownloading )
                    {
                        toolbox.cancelDownload();
                    }
                    else
                    {
                        toolbox.activePackage = model
                        // toolbox.activePackage = model;
                        if ( model.can_upgrade )
                        {
                            // toolbox.downloadAndInstallPlugin( model.update_url );
                        }
                        else
                        {
                            toolbox.startDownload( model.download_url );
                        }
                    }
                }
            }
        }
    }

    Item
    {
        id: supportedConfigsChart
        anchors.top: normalData.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        height: visible ? childrenRect.height : 0
        width: normalData.width
        visible: model.type == "material" && model.supported_configs.length > 0
        Label
        {
            id: compatibilityHeading
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            text: catalog.i18nc("@label", "Compatibility")
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("default")
        }
        Column
        {
            id: compatibilityLabels
            anchors
            {
                top: compatibilityHeading.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottomMargin: UM.Theme.getSize("default_margin").height
            }
            width: childrenRect.width
            Label
            {
                text: catalog.i18nc("@label", "Machines") + ":"
                font: UM.Theme.getFont("small")
            }
            Label
            {
                text: catalog.i18nc("@label", "Print Cores") + ":"
                font: UM.Theme.getFont("small")
            }
            Label
            {
                text: catalog.i18nc("@label", "Quality Profiles") + ":"
                font: UM.Theme.getFont("small")
            }
        }
        Column
        {
            id: compatibilityValues
            anchors
            {
                left: compatibilityLabels.right
                leftMargin: UM.Theme.getSize("default_margin").height
                top: compatibilityLabels.top
                bottom: compatibilityLabels.bottom
            }
            Label
            {
                text: "Thingy"
                font: UM.Theme.getFont("very_small")
            }
            Label
            {
                text: "Thingy"
                font: UM.Theme.getFont("very_small")
            }
            Label
            {
                text: "Thingy"
                font: UM.Theme.getFont("very_small")
            }
        }
    }

    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: tile.width
        height: UM.Theme.getSize("default_lining").height
        anchors.bottom: tile.bottom
    }
    Connections
    {
        target: toolbox
        onInstallChanged: installed = toolbox.isInstalled(model.id)
    }
}

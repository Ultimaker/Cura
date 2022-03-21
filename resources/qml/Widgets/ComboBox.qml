// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// ComboBox with Cura styling.
//
ComboBox
{
    id: control

    property var defaultTextOnEmptyModel: catalog.i18nc("@label", "No items to select from")  // Text displayed in the combobox when the model is empty
    property var defaultTextOnEmptyIndex: ""  // Text displayed in the combobox when the model has items but no item is selected
    enabled: delegateModel.count > 0

    onVisibleChanged: { popup.close() }

    states: [
        State
        {
            name: "disabled"
            when: !control.enabled
            PropertyChanges { target: background; color: UM.Theme.getColor("setting_control_disabled")}
            PropertyChanges { target: contentLabel; color: UM.Theme.getColor("setting_control_disabled_text")}
        },
        State
        {
            name: "highlighted"
            when: control.hovered || control.activeFocus
            PropertyChanges { target: background; liningColor: UM.Theme.getColor("border_main")}
        }
    ]

    background: UM.UnderlineBackground{}

    indicator: UM.RecolorImage
    {
        id: downArrow
        x: control.width - width - control.rightPadding
        y: control.topPadding + Math.round((control.availableHeight - height) / 2)

        source: UM.Theme.getIcon("ChevronSingleDown")
        width: UM.Theme.getSize("standard_arrow").width
        height: UM.Theme.getSize("standard_arrow").height
        sourceSize.width: width + 5 * screenScaleFactor
        sourceSize.height: width + 5 * screenScaleFactor

        color: UM.Theme.getColor("setting_control_button")
    }

    contentItem: UM.Label
    {
        id: contentLabel
        leftPadding: UM.Theme.getSize("setting_unit_margin").width + UM.Theme.getSize("default_margin").width
        anchors.right: downArrow.left
        wrapMode: Text.NoWrap
        text:
        {
            if (control.delegateModel.count == 0)
            {
                return control.defaultTextOnEmptyModel != "" ? control.defaultTextOnEmptyModel : control.defaultTextOnEmptyIndex
            }
            else
            {
                return control.currentIndex == -1 ? control.defaultTextOnEmptyIndex : control.currentText
            }
        }

        textFormat: Text.PlainText
        color: control.currentIndex == -1 ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
        elide: Text.ElideRight
    }

    popup: Popup
    {
        y: control.height - UM.Theme.getSize("default_lining").height
        width: control.width
        implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
        bottomMargin: UM.Theme.getSize("default_margin").height
        padding: UM.Theme.getSize("default_lining").width

        contentItem: ListView
        {
            implicitHeight: contentHeight

            ScrollBar.vertical: UM.ScrollBar {}
            clip: true
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
        }

        background: Rectangle
        {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
    }

    delegate: ItemDelegate
    {
        id: delegateItem
        width: control.width - 2 * UM.Theme.getSize("default_lining").width
        height: control.height
        highlighted: control.highlightedIndex == index
        text:
        // FIXME: Maybe there is a better way to do this. Check model and modelData doc page:
        // https://doc.qt.io/qt-5/qtquick-modelviewsdata-modelview.html
        {
            var _val = undefined
            if (typeof _val === 'undefined')  // try to get textRole from "model".
            {
                _val = model[textRole]
            }
            if (typeof _val === 'undefined')  // try to get textRole from "modelData" if it's still undefined.
            {
                _val = modelData[textRole]
            }
            return (typeof _val !== 'undefined') ? _val : ""
        }

        contentItem: UM.Label
        {
            id: delegateLabel
            // FIXME: Somehow the top/bottom anchoring is not correct on Linux and it results in invisible texts.
            anchors.fill: parent
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

            text: delegateItem.text
            textFormat: Text.PlainText
            color: UM.Theme.getColor("setting_control_text")
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
        }

        background: UM.TooltipArea
        {
            Rectangle
            {
                color: delegateItem.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
                anchors.fill: parent
            }
            text: delegateLabel.truncated ? delegateItem.text : ""
        }
    }
}

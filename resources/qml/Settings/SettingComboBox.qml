// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

SettingItem
{
    id: base

    ComboBox
    {
//         signal valueChanged(string value);
//         id: base
        model: definition.options
        textRole: "name";

        MouseArea
        {
            anchors.fill: parent;
            acceptedButtons: Qt.NoButton;
            onWheel: wheel.accepted = true;
        }

        style: ComboBoxStyle
        {
            background: Rectangle
            {
                color:
                {
                    if (!enabled)
                    {
                        return base.style.controlDisabledColor
                    }
                    if(control.hovered || base.activeFocus)
                    {
                        return base.style.controlHighlightColor
                    }
                    else
                    {
                        return base.style.controlColor
                    }
                }
                border.width: base.style.controlBorderWidth;
                border.color: !enabled ? base.style.controlDisabledBorderColor : control.hovered ? base.style.controlBorderHighlightColor : base.style.controlBorderColor;
            }
            label: Item
            {
                Label
                {
                    anchors.left: parent.left;
                    anchors.leftMargin: base.style.controlBorderWidth
                    anchors.right: downArrow.left;
                    anchors.rightMargin: base.style.controlBorderWidth;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.currentText;
                    font: base.style.controlFont;
                    color: !enabled ? base.style.controlDisabledTextColor : base.style.controlTextColor;

                    elide: Text.ElideRight;
                    verticalAlignment: Text.AlignVCenter;
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.right: parent.right;
                    anchors.rightMargin: base.style.controlBorderWidth * 2;
                    anchors.verticalCenter: parent.verticalCenter;

                    source: UM.Theme.getIcon("arrow_bottom")
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5
                    sourceSize.height: width + 5

                    color: base.style.controlTextColor;

                }
            }
        }
/*
        onActivated: {
            valueChanged(options.getItem(index).value);
        }

        onModelChanged: {
            updateCurrentIndex();
        }

        Component.onCompleted: {
            parent.parent.valueChanged.connect(updateCurrentIndex)
        }

        function updateCurrentIndex() {
            if (!options) {
                return;
            }

            for(var i = 0; i < options.rowCount(); ++i) {
                if(options.getItem(i).value == value) {
                    currentIndex = i;
                    return;
                }
            }

            currentIndex = -1;
        }*/
    }
}

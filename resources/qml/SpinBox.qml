// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.15

Item
{
    id: base

    height: spinBox.height

    property string prefix: ""
    property string suffix: ""
    property int decimals: 0
    property real stepSize: 1
    property real value: 0
    property real from: 0
    property real to: 99

    property alias wrap: spinBox.wrap

    property bool editable: true

    property var validator: RegExpValidator
    {
        regExp: new RegExp("^" + prefix + "([0-9]+[.|,]?[0-9]*)?" + suffix + "$")
    }

    signal editingFinished()

    SpinBox
    {
        id: spinBox
        anchors.fill: base

        stepSize: 1

        value: Math.floor(base.value / base.stepSize)
        from: Math.floor(base.from / base.stepSize)
        to: Math.floor(base.to / base.stepSize)
        editable: base.editable

        valueFromText: function(text)
        {
            return parseFloat(text.substring(prefix.length, text.length - suffix.length)) / base.stepSize;
        }

        textFromValue: function(value)
        {
            return prefix + (value * base.stepSize).toFixed(decimals) + suffix;
        }

        validator: base.validator

        onValueModified:
        {
            base.value = value * base.stepSize;
        }

        contentItem: TextField
        {
            text: spinBox.textFromValue(spinBox.value, spinBox.locale)
            selectByMouse: base.editable
            background: Item {}
            validator: base.validator

            onActiveFocusChanged:
            {
                if(!activeFocus)
                {
                    base.editingFinished();
                }
            }
        }
    }
}

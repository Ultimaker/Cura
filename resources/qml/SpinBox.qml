// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.15

SpinBox
{
    id: base

    property string prefix: ""
    property string suffix: ""
    property int decimals: 0

    signal editingFinished()

    valueFromText: function(text)
    {
        return parseFloat(text.substring(prefix.length, text.length - suffix.length), decimals);
    }

    textFromValue: function(value)
    {
        return prefix + value.toFixed(decimals) + suffix
    }

    validator: RegExpValidator
    {
        regExp: new RegExp("^" + prefix + "([0-9]+[.|,]?[0-9]*)?" + suffix + "$")
    }

    contentItem: TextField
    {
        text: base.textFromValue(base.value, base.locale)
        selectByMouse: true
        background: Item {}
        validator: base.validator

        onActiveFocusChanged:
        {
            if(!activeFocus)
            {
                base.editingFinished()
            }
        }
    }
}
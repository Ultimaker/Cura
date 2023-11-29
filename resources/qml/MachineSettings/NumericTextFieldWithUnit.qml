// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// TextField widget with validation for editing numeric data in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: numericTextFieldWithUnit

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width

    property int controlWidth: UM.Theme.getSize("setting_control").width
    property int controlHeight: UM.Theme.getSize("setting_control").height
    property real spacing: UM.Theme.getSize("default_margin").width

    text: tooltipText

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias propertyProvider: propertyProvider
    property alias labelText: fieldLabel.text
    property alias labelFont: fieldLabel.font
    property alias labelWidth: fieldLabel.width
    property alias unitText: unitLabel.text

    property alias textField: textFieldWithUnit
    property alias valueText: textFieldWithUnit.text
    property alias enabled: textFieldWithUnit.enabled
    property alias editingFinishedFunction: textFieldWithUnit.editingFinishedFunction

    property string tooltipText: propertyProvider.properties.description ? propertyProvider.properties.description : ""

    property real minimum: 0
    property real maximum: Number.POSITIVE_INFINITY
    property int decimals: 6

    // callback functions
    property var afterOnEditingFinishedFunction: dummy_func
    property var forceUpdateOnChangeFunction: dummy_func
    property var setValueFunction: null

    // a dummy function for default property values
    function dummy_func() {}


    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description", "validationState" ]
    }

    UM.Label
    {
        id: fieldLabel
        anchors.left: parent.left
        anchors.verticalCenter: textFieldWithUnit.verticalCenter
        visible: text != ""
    }

    TextField
    {
        id: textFieldWithUnit
        anchors.left: fieldLabel.right
        anchors.leftMargin: spacing
        verticalAlignment: Text.AlignVCenter

        // The control is set up for left to right. So we force it to that. If we don't, it will take the OS reading
        // direction, which might not be left to right. This will lead to the text overlapping with the unit
        horizontalAlignment: TextInput.AlignLeft

        selectionColor: UM.Theme.getColor("text_selection")
        selectedTextColor: UM.Theme.getColor("setting_control_text")
        padding: 0
        leftPadding: UM.Theme.getSize("narrow_margin").width
        width: numericTextFieldWithUnit.controlWidth
        height: numericTextFieldWithUnit.controlHeight

        // Background is a rounded-cornered box with filled color as state indication (normal, warning, error, etc.)
        background: UM.UnderlineBackground
        {
            anchors.fill: parent

            borderColor: textFieldWithUnit.activeFocus ? UM.Theme.getColor("text_field_border_active") : "transparent"
            liningColor:
            {
                if (!textFieldWithUnit.enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled_border");
                }
                switch (propertyProvider.properties.validationState)
                {
                    case "ValidatorState.Exception":
                    case "ValidatorState.MinimumError":
                    case "ValidatorState.MaximumError":
                        return UM.Theme.getColor("setting_validation_error")
                    case "ValidatorState.MinimumWarning":
                    case "ValidatorState.MaximumWarning":
                        return UM.Theme.getColor("setting_validation_warning")
                }
                // Validation is OK.
                if(textFieldWithUnit.activeFocus)
                {
                    return UM.Theme.getColor("text_field_border_active");
                }
                if(textFieldWithUnit.hovered)
                {
                    return UM.Theme.getColor("text_field_border_hovered");
                }
                return UM.Theme.getColor("border_field_light");
            }

            color:
            {
                if (!textFieldWithUnit.enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled")
                }
                switch (propertyProvider.properties.validationState)
                {
                    case "ValidatorState.Exception":
                    case "ValidatorState.MinimumError":
                    case "ValidatorState.MaximumError":
                        return UM.Theme.getColor("setting_validation_error_background")
                    case "ValidatorState.MinimumWarning":
                    case "ValidatorState.MaximumWarning":
                        return UM.Theme.getColor("setting_validation_warning_background")
                    case "ValidatorState.Valid":
                        return UM.Theme.getColor("setting_validation_ok")
                    default:
                        return UM.Theme.getColor("setting_control")
                }
            }
        }

        hoverEnabled: true
        selectByMouse: true
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering

        // When the textbox gets focused by TAB, select all text
        onActiveFocusChanged:
        {
            if (activeFocus && (focusReason == Qt.TabFocusReason || focusReason == Qt.BacktabFocusReason))
            {
                selectAll()
            }
        }

        text:
        {
            const value = propertyProvider.properties.value
            return value ? value : ""
        }
        property string validatorString:
        {
            var digits = Math.min(8, 1 + Math.floor(
                Math.log(Math.max(Math.abs(numericTextFieldWithUnit.maximum), Math.abs(numericTextFieldWithUnit.minimum)))/Math.log(10)
            ))
            var minus = numericTextFieldWithUnit.minimum < 0 ? "-?" : ""
            if (numericTextFieldWithUnit.decimals == 0)
            {
                return "^%0\\d{1,%1}$".arg(minus).arg(digits)
            }
            else
            {
                return "^%0\\d{0,%1}[.,]?\\d{0,%2}$".arg(minus).arg(digits).arg(numericTextFieldWithUnit.decimals)
            }
        }
        validator: RegularExpressionValidator
        {
            regularExpression: new RegExp(textFieldWithUnit.validatorString)
        }

        //Enforce actual minimum and maximum values.
        //The DoubleValidator allows intermediate values, which essentially means that the maximum gets rounded up to the nearest power of 10.
        //This is not accurate at all, so here if the value exceeds the maximum or the minimum we disallow it.
        property string previousText
        onTextChanged:
        {
            var value = Number(text);
            if(value < numericTextFieldWithUnit.minimum || value > numericTextFieldWithUnit.maximum)
            {
                text = previousText;
            }
            previousText = text;
        }

        onEditingFinished: editingFinishedFunction()

        property var editingFinishedFunction: defaultEditingFinishedFunction

        function defaultEditingFinishedFunction()
        {
            if (propertyProvider && text != propertyProvider.properties.value)
            {
                // For some properties like the extruder-compatible material diameter, they need to
                // trigger many updates, such as the available materials, the current material may
                // need to be switched, etc. Although setting the diameter can be done directly via
                // the provider, all the updates that need to be triggered then need to depend on
                // the metadata update, a signal that can be fired way too often. The update functions
                // can have if-checks to filter out the irrelevant updates, but still it incurs unnecessary
                // overhead.
                // The ExtruderStack class has a dedicated function for this call "setCompatibleMaterialDiameter()",
                // and it triggers the diameter update signals only when it is needed. Here it is optionally
                // choose to use setCompatibleMaterialDiameter() or other more specific functions that
                // are available.
                if (setValueFunction !== null)
                {
                    setValueFunction(text)
                }
                else
                {
                    propertyProvider.setPropertyValue("value", text)
                }
                forceUpdateOnChangeFunction()
                afterOnEditingFinishedFunction()
            }
        }

        UM.Label
        {
            id: unitLabel
            anchors.right: parent.right
            anchors.rightMargin: Math.round(UM.Theme.getSize("setting_unit_margin").width)
            anchors.verticalCenter: parent.verticalCenter
            text: unitText
            textFormat: Text.PlainText
            color: UM.Theme.getColor("setting_unit")
        }
    }
}

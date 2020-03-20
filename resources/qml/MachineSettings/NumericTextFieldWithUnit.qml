// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
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
    property alias valueValidator: textFieldWithUnit.validator
    property alias editingFinishedFunction: textFieldWithUnit.editingFinishedFunction

    property string tooltipText: propertyProvider.properties.description

    // whether negative value is allowed. This affects the validation of the input field.
    property bool allowNegativeValue: false
    // whether positive value is allowed. This affects the validation of the input field.
    property bool allowPositiveValue: true

    // callback functions
    property var afterOnEditingFinishedFunction: dummy_func
    property var forceUpdateOnChangeFunction: dummy_func
    property var setValueFunction: null

    // a dummy function for default property values
    function dummy_func() {}


    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    Label
    {
        id: fieldLabel
        anchors.left: parent.left
        anchors.verticalCenter: textFieldWithUnit.verticalCenter
        visible: text != ""
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
    }

    TextField
    {
        id: textFieldWithUnit
        anchors.left: fieldLabel.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        verticalAlignment: Text.AlignVCenter
        width: numericTextFieldWithUnit.controlWidth
        height: numericTextFieldWithUnit.controlHeight

        // Background is a rounded-cornered box with filled color as state indication (normal, warning, error, etc.)
        background: Rectangle
        {
            anchors.fill: parent
            anchors.margins: Math.round(UM.Theme.getSize("default_lining").width)
            radius: UM.Theme.getSize("setting_control_radius").width

            border.color:
            {
                if (!textFieldWithUnit.enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled_border")
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
                if (textFieldWithUnit.hovered || textFieldWithUnit.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_border_highlight")
                }
                return UM.Theme.getColor("setting_control_border")
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
        validator: DoubleValidator
        {
            bottom: allowNegativeValue ? Number.NEGATIVE_INFINITY : 0
            top: allowPositiveValue ? Number.POSITIVE_INFINITY : 0
            decimals: 6
            notation: DoubleValidator.StandardNotation
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

        Label
        {
            id: unitLabel
            anchors.right: parent.right
            anchors.rightMargin: Math.round(UM.Theme.getSize("setting_unit_margin").width)
            anchors.verticalCenter: parent.verticalCenter
            text: unitText
            textFormat: Text.PlainText
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
            color: UM.Theme.getColor("setting_unit")
            font: UM.Theme.getFont("default")
        }
    }
}

// Copyright (c) 2025 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.7 as UM

// Custom multiline text area component for post-processing script settings
// Triggered when setting has "comments": "multiline" property
Item
{
    id: base

    // Properties passed from the Loader
    property var definition
    property var settingDefinitionsModel
    property var propertyProvider
    property var globalPropertyProvider
    
    // Standard setting item properties (required by loader but unused in this component)
    property bool showRevertButton: false
    property bool showInheritButton: false
    property bool showLinkedSettingIcon: false
    property bool doDepthIndentation: false
    property bool doQualityUserSettingEmphasis: false

    // Internal state tracking (unused but kept for potential future use)
    property string textBeforeEdit
    property bool textHasChanged

    // Signals for tooltip support (required by Connections in loader)
    signal showTooltip(string text)
    signal hideTooltip()

    width: parent.width
    // Height calculation: label height + spacing + text area (3x normal height for multiline editing)
    height: UM.Theme.getSize("standard_list_lineheight").height + UM.Theme.getSize("narrow_margin").height + (UM.Theme.getSize("setting_control").height * 3)

    UM.Label
    {
        id: labelText
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: UM.Theme.getSize("standard_list_lineheight").height
        text: definition ? definition.label : ""
        elide: Text.ElideRight
        font: UM.Theme.getFont("default_bold")
        color: UM.Theme.getColor("text")
    }

    Flickable
    {
        id: flickable
        anchors.top: labelText.bottom
        anchors.topMargin: UM.Theme.getSize("narrow_margin").height
        anchors.left: parent.left
        anchors.right: parent.right
        // Right margin to prevent overlap with parent ListView scrollbar
        anchors.rightMargin: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
        height: UM.Theme.getSize("setting_control").height * 3
        
        clip: true
        ScrollBar.vertical: UM.ScrollBar { }
        
        TextArea.flickable: TextArea
        {
            id: textArea
            
            enabled: propertyProvider && propertyProvider.properties ? propertyProvider.properties.enabled === "True" : true
            // Explicit undefined check to prevent QML warnings about undefined QString assignment
            text: (propertyProvider && propertyProvider.properties && propertyProvider.properties.value !== undefined) ? propertyProvider.properties.value : ""
            
            background: Rectangle
            {
                color: UM.Theme.getColor("setting_control")
                border.color: textArea.activeFocus ? UM.Theme.getColor("text_field_border_active") : UM.Theme.getColor("text_field_border")
                border.width: UM.Theme.getSize("default_lining").width
            }

            onTextChanged:
            {
                // Save value on each keystroke when focused (live update)
                if (activeFocus && propertyProvider)
                {
                    propertyProvider.setPropertyValue("value", text);
                }
            }

            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            selectionColor: UM.Theme.getColor("text_selection")
            selectedTextColor: UM.Theme.getColor("text")
            wrapMode: TextEdit.NoWrap
            selectByMouse: true

            // Allow Enter/Return to insert newlines instead of closing dialog
            Keys.onReturnPressed: function(event) { event.accepted = false; }
            Keys.onEnterPressed: function(event) { event.accepted = false; }
            // Escape key removes focus from text area
            Keys.onEscapePressed: function(event) { focus = false; event.accepted = true; }
        }
    }
}

// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.PreferencesPage
{
    //: General configuration page title
    title: catalog.i18nc("@title:tab", "General")
    id: generalPreferencesPage

    width: parent ? parent.width: 0

    function setDefaultLanguage(languageCode)
    {
        //loops through the languageList and sets the language using the languageCode
        for(var i = 0; i < languageList.count; i++)
        {
            if (languageComboBox.model.get(i).code == languageCode)
            {
                languageComboBox.currentIndex = i
            }
        }
    }

    function setDefaultTheme(defaultThemeCode)
    {
        for(var i = 0; i < themeList.count; i++)
        {
            if (themeComboBox.model.get(i).code == defaultThemeCode)
            {
                themeComboBox.currentIndex = i
            }
        }
    }

    function setDefaultDiscardOrKeepProfile(code)
    {
        for (var i = 0; i < choiceOnProfileOverrideDropDownButton.model.count; i++)
        {
            if (choiceOnProfileOverrideDropDownButton.model.get(i).code == code)
            {
                choiceOnProfileOverrideDropDownButton.currentIndex = i;
                break;
            }
        }
    }

    function setDefaultOpenProjectOption(code)
    {
        for (var i = 0; i < choiceOnOpenProjectDropDownButton.model.count; ++i)
        {
            if (choiceOnOpenProjectDropDownButton.model.get(i).code == code)
            {
                choiceOnOpenProjectDropDownButton.currentIndex = i
                break;
            }
        }
    }

    function reset()
    {
        UM.Preferences.resetPreference("general/language")
        var defaultLanguage = UM.Preferences.getValue("general/language")
        setDefaultLanguage(defaultLanguage)

        UM.Preferences.resetPreference("general/theme")
        var defaultTheme = UM.Preferences.getValue("general/theme")
        setDefaultTheme(defaultTheme)

        UM.Preferences.resetPreference("general/use_tray_icon")
        trayIconCheckbox.checked = boolCheck(UM.Preferences.getValue("cura/use_tray_icon"))

        UM.Preferences.resetPreference("cura/single_instance")
        singleInstanceCheckbox.checked = boolCheck(UM.Preferences.getValue("cura/single_instance"))
        UM.Preferences.resetPreference("cura/single_instance_clear_before_load")
        singleInstanceClearBeforeLoadCheckbox.checked = boolCheck(UM.Preferences.getValue("cura/single_instance_clear_before_load"))

        UM.Preferences.resetPreference("physics/automatic_push_free")
        pushFreeCheckbox.checked = boolCheck(UM.Preferences.getValue("physics/automatic_push_free"))
        UM.Preferences.resetPreference("physics/automatic_drop_down")
        dropDownCheckbox.checked = boolCheck(UM.Preferences.getValue("physics/automatic_drop_down"))
        UM.Preferences.resetPreference("mesh/scale_to_fit")
        scaleToFitCheckbox.checked = boolCheck(UM.Preferences.getValue("mesh/scale_to_fit"))
        UM.Preferences.resetPreference("mesh/scale_tiny_meshes")
        scaleTinyCheckbox.checked = boolCheck(UM.Preferences.getValue("mesh/scale_tiny_meshes"))
        UM.Preferences.resetPreference("cura/select_models_on_load")
        selectModelsOnLoadCheckbox.checked = boolCheck(UM.Preferences.getValue("cura/select_models_on_load"))
        UM.Preferences.resetPreference("cura/jobname_prefix")
        prefixJobNameCheckbox.checked = boolCheck(UM.Preferences.getValue("cura/jobname_prefix"))
        UM.Preferences.resetPreference("view/show_overhang");
        showOverhangCheckbox.checked = boolCheck(UM.Preferences.getValue("view/show_overhang"))
        UM.Preferences.resetPreference("view/show_xray_warning");
        showXrayErrorCheckbox.checked = boolCheck(UM.Preferences.getValue("view/show_xray_warning"))
        UM.Preferences.resetPreference("view/center_on_select");
        centerOnSelectCheckbox.checked = boolCheck(UM.Preferences.getValue("view/center_on_select"))
        UM.Preferences.resetPreference("view/invert_zoom");
        invertZoomCheckbox.checked = boolCheck(UM.Preferences.getValue("view/invert_zoom"))
        UM.Preferences.resetPreference("view/navigation_style");
        UM.Preferences.resetPreference("view/zoom_to_mouse");
        zoomToMouseCheckbox.checked = boolCheck(UM.Preferences.getValue("view/zoom_to_mouse"))
        //UM.Preferences.resetPreference("view/top_layer_count");
        //topLayerCountCheckbox.checked = boolCheck(UM.Preferences.getValue("view/top_layer_count"))
        UM.Preferences.resetPreference("general/restore_window_geometry")
        restoreWindowPositionCheckbox.checked = boolCheck(UM.Preferences.getValue("general/restore_window_geometry"))

        UM.Preferences.resetPreference("tool/flip_y_axis_tool_handle")
        flipToolhandleYCheckbox.checked = boolcheck(UM.Preferences.getValue("tool/flip_y_axis_tool_handle"))

        UM.Preferences.resetPreference("general/camera_perspective_mode")
        //var defaultCameraMode = UM.Preferences.getValue("general/camera_perspective_mode")
//        /setDefaultCameraMode(defaultCameraMode)

        UM.Preferences.resetPreference("cura/choice_on_profile_override")
        setDefaultDiscardOrKeepProfile(UM.Preferences.getValue("cura/choice_on_profile_override"))

        UM.Preferences.resetPreference("cura/choice_on_open_project")
        setDefaultOpenProjectOption(UM.Preferences.getValue("cura/choice_on_open_project"))

        UM.Preferences.resetPreference("info/send_slice_info")
        sendDataCheckbox.checked = boolCheck(UM.Preferences.getValue("info/send_slice_info"))

        UM.Preferences.resetPreference("info/send_engine_crash")
        sendEngineCrashCheckbox.checked = boolCheck(UM.Preferences.getValue("info/send_engine_crash"))

        UM.Preferences.resetPreference("info/anonymous_engine_crash_report")
        sendEngineCrashCheckboxAnonymous.checked = boolCheck(UM.Preferences.getValue("info/anonymous_engine_crash_report"))

        UM.Preferences.resetPreference("info/automatic_update_check")
        checkUpdatesCheckbox.checked = boolCheck(UM.Preferences.getValue("info/automatic_update_check"))

        UM.Preferences.resetPreference("info/latest_update_source")
        UM.Preferences.resetPreference("info/automatic_plugin_update_check")
        pluginNotificationsUpdateCheckbox.checked = boolCheck(UM.Preferences.getValue("info/automatic_plugin_update_check"))
    }

    buttons: [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Defaults")
            onClicked: reset()
        }
    ]
    ScrollView
    {
        id: preferencesScrollView
        width: parent.width
        height: parent.height

        ScrollBar.vertical: UM.ScrollBar
        {
            id: preferencesScrollBar
            parent: preferencesScrollView.parent
            anchors
            {
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }

            onPositionChanged: {
                // This removes focus from items when scrolling.
                // This fixes comboboxes staying open and scrolling container
                if (!activeFocus) {
                    forceActiveFocus();
                }
            }
        }

        Column
        {
            UM.I18nCatalog{id: catalog; name: "cura"}
            width: preferencesScrollView.width - preferencesScrollBar.width

            UM.Label
            {
                font: UM.Theme.getFont("medium_bold")
                text: catalog.i18nc("@label", "Interface")
            }

            GridLayout
            {
                id: interfaceGrid
                columns: 2
                width: parent.width

                UM.Label
                {
                    id: languageLabel
                    text: "Language*:" //Don't translate this, to make it easier to find the language drop-down if you can't read the current language.
                }

                ListModel
                {
                    id: languageList

                    Component.onCompleted:
                    {
                        append({ text: "English", code: "en_US" })
                        append({ text: "Čeština", code: "cs_CZ" })
                        append({ text: "Deutsch", code: "de_DE" })
                        append({ text: "Español", code: "es_ES" })
                        append({ text: "Français", code: "fr_FR" })
                        append({ text: "Italiano", code: "it_IT" })
                        append({ text: "日本語", code: "ja_JP" })
                        append({ text: "한국어", code: "ko_KR" })
                        append({ text: "Nederlands", code: "nl_NL" })
                        append({ text: "Português do Brasil", code: "pt_BR" })
                        append({ text: "Português", code: "pt_PT" })
                        append({ text: "Русский", code: "ru_RU" })
                        append({ text: "Türkçe", code: "tr_TR" })
                        append({ text: "简体中文", code: "zh_CN" })

                        var date_object = new Date();
                        if (date_object.getUTCMonth() == 8 && date_object.getUTCDate() == 19) //Only add Pirate on the 19th of September.
                        {
                            append({ text: "Pirate", code: "en_7S" })
                        }

                        // incomplete and/or abandoned
                        append({ text: catalog.i18nc("@heading", "-- incomplete --"), code: "" })
                        append({ text: "正體字", code: "zh_TW" })
                        append({ text: "Magyar", code: "hu_HU" })
                        append({ text: "Suomi", code: "fi_FI" })
                        append({ text: "Polski", code: "pl_PL" })
                    }
                }

                Cura.ComboBox
                {
                    id: languageComboBox

                    textRole: "text"
                    model: languageList
                    implicitWidth: UM.Theme.getSize("combobox").width
                    height: currencyField.height

                    function setCurrentIndex() {
                        var code = UM.Preferences.getValue("general/language");
                        for(var i = 0; i < languageList.count; ++i)
                        {
                            if(model.get(i).code == code)
                            {
                                return i
                            }
                        }
                    }

                    currentIndex: setCurrentIndex()

                    onActivated:
                    {
                        if (model.get(index).code != "")
                        {
                            UM.Preferences.setValue("general/language", model.get(index).code);
                        }
                        else
                        {
                            currentIndex = setCurrentIndex();
                        }
                    }
                }

                UM.Label
                {
                    id: currencyLabel
                    text: catalog.i18nc("@label", "Currency:")
                }

                Cura.TextField
                {
                    id: currencyField
                    selectByMouse: true
                    text: UM.Preferences.getValue("cura/currency")
                    implicitWidth: UM.Theme.getSize("combobox").width
                    implicitHeight: UM.Theme.getSize("setting_control").height
                    onTextChanged: UM.Preferences.setValue("cura/currency", text)
                }

                UM.Label
                {
                    id: themeLabel
                    text: catalog.i18nc("@label: Please keep the asterix, it's to indicate that a restart is needed.", "Theme*:")
                }

                ListModel
                {
                    id: themeList

                    Component.onCompleted: {
                        var themes = UM.Theme.getThemes()
                        for (var i = 0; i < themes.length; i++)
                        {
                            append({ text: themes[i].name.toString(), code: themes[i].id.toString() });
                        }
                    }
                }

                Cura.ComboBox
                {
                    id: themeComboBox

                    model: themeList
                    textRole: "text"
                    implicitWidth: UM.Theme.getSize("combobox").width
                    height: currencyField.height

                    currentIndex:
                    {
                        var code = UM.Preferences.getValue("general/theme");
                        for(var i = 0; i < themeList.count; ++i)
                        {
                            if(model.get(i).code == code)
                            {
                                return i
                            }
                        }
                        return 0;
                    }
                    onActivated: UM.Preferences.setValue("general/theme", model.get(index).code)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;

                text: catalog.i18nc("@info:tooltip", "Slice automatically when changing settings.")

                UM.CheckBox
                {
                    id: autoSliceCheckbox
                    checked: boolCheck(UM.Preferences.getValue("general/auto_slice"))
                    onClicked: UM.Preferences.setValue("general/auto_slice", checked)

                    text: catalog.i18nc("@option:check", "Slice automatically");
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;

                text: catalog.i18nc("@info:tooltip", "Show an icon and notifications in the system notification area.")

                UM.CheckBox
                {
                    id: trayIconCheckbox
                    checked: boolCheck(UM.Preferences.getValue("general/use_tray_icon"))
                    onClicked: UM.Preferences.setValue("general/use_tray_icon", checked)

                    text: catalog.i18nc("@option:check", "Add icon to system tray *");
                }
            }

            UM.Label
            {
                id: languageCaption

                //: Language change warning
                text: catalog.i18nc("@label", "*You will need to restart the application for these changes to have effect.")
                wrapMode: Text.WordWrap
                font.italic: true

            }

            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").width
            }

            UM.Label
            {
                font: UM.Theme.getFont("medium_bold")
                text: catalog.i18nc("@label", "Viewport behavior")
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;

                text: catalog.i18nc("@info:tooltip", "Highlight unsupported areas of the model in red. Without support these areas will not print properly.")

                UM.CheckBox
                {
                    id: showOverhangCheckbox

                    checked: boolCheck(UM.Preferences.getValue("view/show_overhang"))
                    onClicked: UM.Preferences.setValue("view/show_overhang", checked)

                    text: catalog.i18nc("@option:check", "Display overhang");
                }
            }


            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;

                text: catalog.i18nc("@info:tooltip", "Highlight missing or extraneous surfaces of the model using warning signs. The toolpaths will often be missing parts of the intended geometry.")

                UM.CheckBox
                {
                    id: showXrayErrorCheckbox

                    checked: boolCheck(UM.Preferences.getValue("view/show_xray_warning"))
                    onClicked: UM.Preferences.setValue("view/show_xray_warning",  checked)

                    text: catalog.i18nc("@option:check", "Display model errors");
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;
                text: catalog.i18nc("@info:tooltip", "Moves the camera so the model is in the center of the view when a model is selected")

                UM.CheckBox
                {
                    id: centerOnSelectCheckbox
                    text: catalog.i18nc("@action:button","Center camera when item is selected");
                    checked: boolCheck(UM.Preferences.getValue("view/center_on_select"))
                    onClicked: UM.Preferences.setValue("view/center_on_select",  checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;
                text: catalog.i18nc("@info:tooltip", "Should the default zoom behavior of cura be inverted?")

                UM.CheckBox
                {
                    id: invertZoomCheckbox
                    text: catalog.i18nc("@action:button", "Invert the direction of camera zoom.");
                    checked: boolCheck(UM.Preferences.getValue("view/invert_zoom"))
                    onClicked: {
                        if(!checked && zoomToMouseCheckbox.checked) //Fix for Github issue Ultimaker/Cura#6490: Make sure the camera origin is in front when unchecking.
                        {
                            UM.Controller.setCameraOrigin("home");
                        }
                        UM.Preferences.setValue("view/invert_zoom", checked);
                    }
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;
                text: zoomToMouseCheckbox.enabled ? catalog.i18nc("@info:tooltip", "Should zooming move in the direction of the mouse?") : catalog.i18nc("@info:tooltip", "Zooming towards the mouse is not supported in the orthographic perspective.")

                UM.CheckBox
                {
                    id: zoomToMouseCheckbox
                    text: catalog.i18nc("@action:button", "Zoom toward mouse direction")
                    checked: boolCheck(UM.Preferences.getValue("view/zoom_to_mouse")) && zoomToMouseCheckbox.enabled
                    onClicked: UM.Preferences.setValue("view/zoom_to_mouse", checked)
                    enabled: UM.Preferences.getValue("general/camera_perspective_mode") !== "orthographic"
                }

                //Because there is no signal for individual preferences, we need to manually link to the onPreferenceChanged signal.
                Connections
                {
                    target: UM.Preferences
                    function onPreferenceChanged(preference)
                    {
                        if(preference != "general/camera_perspective_mode")
                        {
                            return;
                        }
                        zoomToMouseCheckbox.enabled = UM.Preferences.getValue("general/camera_perspective_mode") !== "orthographic";
                        zoomToMouseCheckbox.checked = boolCheck(UM.Preferences.getValue("view/zoom_to_mouse")) && zoomToMouseCheckbox.enabled;
                    }
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should models on the platform be moved so that they no longer intersect?")

                UM.CheckBox
                {
                    id: pushFreeCheckbox
                    text: catalog.i18nc("@option:check", "Ensure models are kept apart")
                    checked: boolCheck(UM.Preferences.getValue("physics/automatic_push_free"))
                    onCheckedChanged: UM.Preferences.setValue("physics/automatic_push_free", checked)
                }
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should models on the platform be moved down to touch the build plate?")

                UM.CheckBox
                {
                    id: dropDownCheckbox
                    text: catalog.i18nc("@option:check", "Automatically drop models to the build plate")
                    checked: boolCheck(UM.Preferences.getValue("physics/automatic_drop_down"))
                    onCheckedChanged:
                    {
                        UM.Preferences.setValue("physics/automatic_drop_down", checked)
                    }
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width;
                height: childrenRect.height;

                text: catalog.i18nc("@info:tooltip","Show caution message in g-code reader.")

                UM.CheckBox
                {
                    id: gcodeShowCautionCheckbox

                    checked: boolCheck(UM.Preferences.getValue("gcodereader/show_caution"))
                    onClicked: UM.Preferences.setValue("gcodereader/show_caution", checked)

                    text: catalog.i18nc("@option:check","Caution message in g-code reader");
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should layer be forced into compatibility mode?")

                UM.CheckBox
                {
                    id: forceLayerViewCompatibilityModeCheckbox
                    text: catalog.i18nc("@option:check", "Force layer view compatibility mode (restart required)")
                    checked: boolCheck(UM.Preferences.getValue("view/force_layer_view_compatibility_mode"))
                    onCheckedChanged: UM.Preferences.setValue("view/force_layer_view_compatibility_mode", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should Cura open at the location it was closed?")

                UM.CheckBox
                {
                    id: restoreWindowPositionCheckbox
                    text: catalog.i18nc("@option:check", "Restore window position on start")
                    checked: boolCheck(UM.Preferences.getValue("general/restore_window_geometry"))
                    onCheckedChanged: UM.Preferences.setValue("general/restore_window_geometry", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "What type of camera rendering should be used?")
                Column
                {
                    spacing: UM.Theme.getSize("narrow_margin").height

                    UM.Label
                    {
                        text: catalog.i18nc("@window:text", "Camera rendering:")
                    }
                    ListModel
                    {
                        id: comboBoxList
                        Component.onCompleted:
                        {
                            append({ text: catalog.i18n("Perspective"), code: "perspective" })
                            append({ text: catalog.i18n("Orthographic"), code: "orthographic" })
                        }
                    }

                    Cura.ComboBox
                    {
                        id: cameraComboBox

                        model: comboBoxList
                        textRole: "text"
                        width: UM.Theme.getSize("combobox").width
                        height: UM.Theme.getSize("combobox").height

                        currentIndex:
                        {
                            var code = UM.Preferences.getValue("general/camera_perspective_mode");
                            for(var i = 0; i < comboBoxList.count; ++i)
                            {
                                if(model.get(i).code == code)
                                {
                                    return i
                                }
                            }
                            return 0
                        }
                        onActivated: UM.Preferences.setValue("general/camera_perspective_mode", model.get(index).code)
                    }
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "What type of camera navigation should be used?")
                Column
                {
                    spacing: UM.Theme.getSize("narrow_margin").height

                    UM.Label
                    {
                        text: catalog.i18nc("@window:text", "Camera navigation:")
                    }
                    ListModel
                    {
                        id: navigationStylesList 
                        Component.onCompleted:
                        {
                            append({ text: "Cura", code: "cura" })
                            append({ text: catalog.i18n("FreeCAD trackpad"), code: "freecad_trackpad" })
                        }
                    }

                    Cura.ComboBox
                    {
                        id: cameraNavigationComboBox

                        model: navigationStylesList 
                        textRole: "text"
                        width: UM.Theme.getSize("combobox").width
                        height: UM.Theme.getSize("combobox").height

                        currentIndex:
                        {
                            var code = UM.Preferences.getValue("view/navigation_style");
                            for(var i = 0; i < comboBoxList.count; ++i)
                            {
                                if(model.get(i).code == code)
                                {
                                    return i
                                }
                            }
                            return 0
                        }
                        onActivated: UM.Preferences.setValue("view/navigation_style", model.get(index).code)
                    }
                }
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should the Y axis of the translate toolhandle be flipped? This will only affect model's Y coordinate, all other settings such as machine Printhead settings are unaffected and still behave as before.")

                UM.CheckBox
                {
                    id: flipToolhandleYCheckbox
                    text: catalog.i18nc("@option:check", "Flip model's toolhandle Y axis (restart required)")
                    checked: boolCheck(UM.Preferences.getValue("tool/flip_y_axis_tool_handle"))
                    onCheckedChanged: UM.Preferences.setValue("tool/flip_y_axis_tool_handle", checked)
                }
            }


            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").height
            }

            UM.Label
            {
                font: UM.Theme.getFont("medium_bold")
                text: catalog.i18nc("@label","Opening and saving files")
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                // Mac only allows applications to run as a single instance, so providing the option for this os doesn't make much sense
                visible: Qt.platform.os !== "osx"
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","Should opening files from the desktop or external applications open in the same instance of Cura?")

                UM.CheckBox
                {
                    id: singleInstanceCheckbox
                    text: catalog.i18nc("@option:check","Use a single instance of Cura")

                    checked: boolCheck(UM.Preferences.getValue("cura/single_instance"))
                    onCheckedChanged: UM.Preferences.setValue("cura/single_instance", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","Should the build plate be cleared before loading a new model in the single instance of Cura?")
                enabled: singleInstanceCheckbox.checked

                UM.CheckBox
                {
                    id: singleInstanceClearBeforeLoadCheckbox
                    text: catalog.i18nc("@option:check","Clear buildplate before loading model into the single instance")
                    checked: boolCheck(UM.Preferences.getValue("cura/single_instance_clear_before_load"))
                    onCheckedChanged: UM.Preferences.setValue("cura/single_instance_clear_before_load", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","Should models be scaled to the build volume if they are too large?")

                UM.CheckBox
                {
                    id: scaleToFitCheckbox
                    text: catalog.i18nc("@option:check","Scale large models")
                    checked: boolCheck(UM.Preferences.getValue("mesh/scale_to_fit"))
                    onCheckedChanged: UM.Preferences.setValue("mesh/scale_to_fit", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","An model may appear extremely small if its unit is for example in meters rather than millimeters. Should these models be scaled up?")

                UM.CheckBox
                {
                    id: scaleTinyCheckbox
                    text: catalog.i18nc("@option:check","Scale extremely small models")
                    checked: boolCheck(UM.Preferences.getValue("mesh/scale_tiny_meshes"))
                    onCheckedChanged: UM.Preferences.setValue("mesh/scale_tiny_meshes", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","Should models be selected after they are loaded?")

                UM.CheckBox
                {
                    id: selectModelsOnLoadCheckbox
                    text: catalog.i18nc("@option:check","Select models when loaded")
                    checked: boolCheck(UM.Preferences.getValue("cura/select_models_on_load"))
                    onCheckedChanged: UM.Preferences.setValue("cura/select_models_on_load", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should a prefix based on the printer name be added to the print job name automatically?")

                UM.CheckBox
                {
                    id: prefixJobNameCheckbox
                    text: catalog.i18nc("@option:check", "Add machine prefix to job name")
                    checked: boolCheck(UM.Preferences.getValue("cura/jobname_prefix"))
                    onCheckedChanged: UM.Preferences.setValue("cura/jobname_prefix", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Should a summary be shown when saving a project file?")

                UM.CheckBox
                {
                    text: catalog.i18nc("@option:check", "Show summary dialog when saving project")
                    checked: boolCheck(UM.Preferences.getValue("cura/dialog_on_project_save"))
                    onCheckedChanged: UM.Preferences.setValue("cura/dialog_on_project_save", checked)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip", "Default behavior when opening a project file")

                Column
                {
                    spacing: UM.Theme.getSize("narrow_margin").height

                    UM.Label
                    {
                        text: catalog.i18nc("@window:text", "Default behavior when opening a project file: ")
                    }

                    Cura.ComboBox
                    {
                        id: choiceOnOpenProjectDropDownButton
                        width: UM.Theme.getSize("combobox").width
                        height: UM.Theme.getSize("combobox").height

                        model: ListModel
                        {
                            id: openProjectOptionModel

                            Component.onCompleted:
                            {
                                append({ text: catalog.i18nc("@option:openProject", "Always ask me this"), code: "always_ask" })
                                append({ text: catalog.i18nc("@option:openProject", "Always open as a project"), code: "open_as_project" })
                                append({ text: catalog.i18nc("@option:openProject", "Always import models"), code: "open_as_model" })
                            }
                        }
                        textRole: "text"

                        currentIndex:
                        {
                            var index = 0;
                            var currentChoice = UM.Preferences.getValue("cura/choice_on_open_project");
                            for (var i = 0; i < model.count; ++i)
                            {
                                if (model.get(i).code == currentChoice)
                                {
                                    index = i;
                                    break;
                                }
                            }
                            return index;
                        }

                        onActivated: UM.Preferences.setValue("cura/choice_on_open_project", model.get(index).code)
                    }
                }
            }

            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").width
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height

                text: catalog.i18nc("@info:tooltip", "When you have made changes to a profile and switched to a different one, a dialog will be shown asking whether you want to keep your modifications or not, or you can choose a default behaviour and never show that dialog again.")

                Column
                {
                    spacing: UM.Theme.getSize("narrow_margin").height

                    UM.Label
                    {
                        font: UM.Theme.getFont("medium_bold")
                        text: catalog.i18nc("@label", "Profiles")
                    }

                    UM.Label
                    {
                        text: catalog.i18nc("@window:text", "Default behavior for changed setting values when switching to a different profile: ")
                    }

                    Cura.ComboBox
                    {
                        id: choiceOnProfileOverrideDropDownButton
                        width: UM.Theme.getSize("combobox_wide").width
                        height: UM.Theme.getSize("combobox_wide").height
                        model: ListModel
                        {
                            id: discardOrKeepProfileListModel

                            Component.onCompleted:
                            {
                                append({ text: catalog.i18nc("@option:discardOrKeep", "Always ask me this"), code: "always_ask" })
                                append({ text: catalog.i18nc("@option:discardOrKeep", "Always discard changed settings"), code: "always_discard" })
                                append({ text: catalog.i18nc("@option:discardOrKeep", "Always transfer changed settings to new profile"), code: "always_keep" })
                            }
                        }
                        textRole: "text"

                        currentIndex:
                        {
                            var index = 0;
                            var code = UM.Preferences.getValue("cura/choice_on_profile_override");
                            for (var i = 0; i < model.count; ++i)
                            {
                                if (model.get(i).code == code)
                                {
                                    index = i;
                                    break;
                                }
                            }
                            return index;
                        }
                        onActivated: UM.Preferences.setValue("cura/choice_on_profile_override", model.get(index).code)
                    }
                }
            }

            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").height
            }

            UM.Label
            {
                font: UM.Theme.getFont("medium_bold")
                text: catalog.i18nc("@label", "Privacy")
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "Should slicing crashes be automatically reported to Ultimaker? Note, no models, IP addresses or other personally identifiable information is sent or stored, unless you give explicit permission.")

                UM.CheckBox
                {
                    id: sendEngineCrashCheckbox
                    text: catalog.i18nc("@option:check","Send engine crash reports")
                    checked: boolCheck(UM.Preferences.getValue("info/send_engine_crash"))
                    onCheckedChanged: UM.Preferences.setValue("info/send_engine_crash", checked)
                }
            }

            ButtonGroup
            {
                id: curaCrashGroup
                buttons: [sendEngineCrashCheckboxAnonymous, sendEngineCrashCheckboxUser]
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "Send crash reports without any personally identifiable information or models data to UltiMaker.")
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                Cura.RadioButton
                {
                    id: sendEngineCrashCheckboxAnonymous
                    text: catalog.i18nc("@option:radio", "Anonymous crash reports")
                    enabled: sendEngineCrashCheckbox.checked && Cura.API.account.isLoggedIn
                    checked: boolCheck(UM.Preferences.getValue("info/anonymous_engine_crash_report"))
                    onClicked: UM.Preferences.setValue("info/anonymous_engine_crash_report", true)
                }
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: Cura.API.account.isLoggedIn ?
                      catalog.i18nc("@info:tooltip", "Send crash reports with your registered UltiMaker account name and the project name to UltiMaker Sentry. No actual model data is being send.") :
                      catalog.i18nc("@info:tooltip", "Please sign in to your UltiMaker account to allow sending non-anonymous data.")
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                Cura.RadioButton
                {
                    id: sendEngineCrashCheckboxUser
                    text: catalog.i18nc("@option:radio", "Include UltiMaker account name")
                    enabled: sendEngineCrashCheckbox.checked && Cura.API.account.isLoggedIn
                    checked: !boolCheck(UM.Preferences.getValue("info/anonymous_engine_crash_report")) && Cura.API.account.isLoggedIn
                    onClicked: UM.Preferences.setValue("info/anonymous_engine_crash_report", false)
                }
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "Should anonymous data about your print be sent to UltiMaker? Note, no models, IP addresses or other personally identifiable information is sent or stored.")

                UM.CheckBox
                {
                    id: sendDataCheckbox
                    text: catalog.i18nc("@option:check","Send (anonymous) print information")
                    checked: boolCheck(UM.Preferences.getValue("info/send_slice_info"))
                    onCheckedChanged: UM.Preferences.setValue("info/send_slice_info", checked)
                }


                UM.SimpleButton
                {
                    onClicked: CuraApplication.showMoreInformationDialogForAnonymousDataCollection()
                    iconSource: UM.Theme.getIcon("Information")
                    anchors.left: sendDataCheckbox.right
                    anchors.verticalCenter: sendDataCheckbox.verticalCenter
                    hoverBackgroundColor: UM.Theme.getColor("secondary_button_hover")
                    backgroundRadius: width / 2
                    height: UM.Theme.getSize("small_button_icon").height
                    color: UM.Theme.getColor("small_button_text")
                    width: height
                }
            }

            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").height
            }

            UM.Label
            {
                font: UM.Theme.getFont("medium_bold")
                text: catalog.i18nc("@label", "Updates")
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "Should Cura check for updates when the program is started?")

                UM.CheckBox
                {
                    id: checkUpdatesCheckbox
                    text: catalog.i18nc("@option:check","Check for updates on start")
                    checked: boolCheck(UM.Preferences.getValue("info/automatic_update_check"))
                    onCheckedChanged: UM.Preferences.setValue("info/automatic_update_check", checked)
                }
            }

            ButtonGroup
            {
                id: curaUpdatesGroup
                buttons: [checkUpdatesOptionBeta, checkUpdatesOptionStable]
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "When checking for updates, only check for stable releases.")
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                Cura.RadioButton
                {
                    id: checkUpdatesOptionStable
                    text: catalog.i18nc("@option:radio", "Stable releases only")
                    enabled: checkUpdatesCheckbox.checked
                    checked: UM.Preferences.getValue("info/latest_update_source") == "stable"
                    onClicked: UM.Preferences.setValue("info/latest_update_source", "stable")
                }
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "When checking for updates, check for both stable and for beta releases.")
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                Cura.RadioButton
                {
                    id: checkUpdatesOptionBeta
                    text: catalog.i18nc("@option:radio", "Stable and Beta releases")
                    enabled: checkUpdatesCheckbox.checked
                    checked: UM.Preferences.getValue("info/latest_update_source") == "beta"
                    onClicked: UM.Preferences.setValue("info/latest_update_source", "beta")
                }
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: visible ? childrenRect.height : 0
                text: catalog.i18nc("@info:tooltip", "Should an automatic check for new plugins be done every time Cura is started? It is highly recommended that you do not disable this!")

                UM.CheckBox
                {
                    id: pluginNotificationsUpdateCheckbox
                    text: catalog.i18nc("@option:check", "Get notifications for plugin updates")
                    checked: boolCheck(UM.Preferences.getValue("info/automatic_plugin_update_check"))
                    onCheckedChanged: UM.Preferences.setValue("info/automatic_plugin_update_check", checked)
                }
            }


            /* Multi-buildplate functionality is disabled because it's broken. See CURA-4975 for the ticket to remove it.
            Item
            {
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").height
            }

            Label
            {
                font.bold: true
                text: catalog.i18nc("@label","Experimental")
            }

            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                text: catalog.i18nc("@info:tooltip","Use multi build plate functionality")

                CheckBox
                {
                    id: useMultiBuildPlateCheckbox
                    text: catalog.i18nc("@option:check","Use multi build plate functionality (restart required)")
                    checked: boolCheck(UM.Preferences.getValue("cura/use_multi_build_plate"))
                    onCheckedChanged: UM.Preferences.setValue("cura/use_multi_build_plate", checked)
                }
            }*/

            Connections
            {
                target: UM.Preferences
                function onPreferenceChanged(preference)
                {
                    if (preference !== "info/send_slice_info")
                    {
                        return;
                    }

                    sendDataCheckbox.checked = boolCheck(UM.Preferences.getValue("info/send_slice_info"))
                }
            }
        }
    }
}

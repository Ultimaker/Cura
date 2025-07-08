# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from collections import OrderedDict

from PyQt6.QtCore import pyqtSlot, Qt

from UM.Application import Application
from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.i18n import i18nCatalog
from UM.Settings.SettingFunction import SettingFunction
from UM.Qt.ListModel import ListModel


class UserChangesModel(ListModel):
    KeyRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2
    ExtruderRole = Qt.ItemDataRole.UserRole + 3
    OriginalValueRole = Qt.ItemDataRole.UserRole + 4
    UserValueRole = Qt.ItemDataRole.UserRole + 6
    CategoryRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.ExtruderRole, "extruder")
        self.addRoleName(self.OriginalValueRole, "original_value")
        self.addRoleName(self.UserValueRole, "user_value")
        self.addRoleName(self.CategoryRole, "category")

        self._i18n_catalog = None

        self._update()

    @pyqtSlot()
    def forceUpdate(self):
        self._update()

    def _update(self):
        application = Application.getInstance()
        machine_manager = application.getMachineManager()
        cura_formula_functions = application.getCuraFormulaFunctions()

        item_dict = OrderedDict()
        item_list = []
        global_stack = machine_manager.activeMachine
        if not global_stack:
            return

        stacks = [global_stack]
        stacks.extend(global_stack.extruderList)

        # Check if the definition container has a translation file and ensure it's loaded.
        definition = global_stack.getBottom()

        definition_suffix = ContainerRegistry.getMimeTypeForContainer(type(definition)).preferredSuffix
        catalog = i18nCatalog(os.path.basename(definition.getId() + "." + definition_suffix))

        if catalog.hasTranslationLoaded():
            self._i18n_catalog = catalog

        for file_name in definition.getInheritedFiles():
            catalog = i18nCatalog(os.path.basename(file_name))
            if catalog.hasTranslationLoaded():
                self._i18n_catalog = catalog

        for stack in stacks:
            # Make a list of all containers in the stack.
            containers = []
            latest_stack = stack
            while latest_stack:
                containers.extend(latest_stack.getContainers())
                latest_stack = latest_stack.getNextStack()

            # Override "getExtruderValue" with "getDefaultExtruderValue" so we can get the default values
            user_changes = containers.pop(0)
            default_value_resolve_context = cura_formula_functions.createContextForDefaultValueEvaluation(stack)

            for setting_key in user_changes.getAllKeys():
                original_value = None

                # Find the category of the instance by moving up until we find a category.
                category = user_changes.getInstance(setting_key).definition
                while category is not None and category.type != "category":
                    category = category.parent

                # Handle translation (and fallback if we weren't able to find any translation files.
                if category is not None:
                    if self._i18n_catalog:
                        category_label = self._i18n_catalog.i18nc(category.key + " label", category.label)
                    else:
                        category_label = category.label
                else:  # Setting is not in any category. Shouldn't happen, but it do. See https://sentry.io/share/issue/d735884370154166bc846904d9b812ff/
                    Logger.error("Setting {key} is not in any setting category.".format(key=setting_key))
                    category_label = ""

                if self._i18n_catalog:
                    label = self._i18n_catalog.i18nc(setting_key + " label", stack.getProperty(setting_key, "label"))
                else:
                    label = stack.getProperty(setting_key, "label")

                for container in containers:
                    if stack == global_stack:
                        resolve = global_stack.getProperty(setting_key, "resolve", default_value_resolve_context)
                        if resolve is not None:
                            original_value = resolve
                            break

                    original_value = container.getProperty(setting_key, "value", default_value_resolve_context)

                    # If a value is a function, ensure it's called with the stack it's in.
                    if isinstance(original_value, SettingFunction):
                        original_value = original_value(stack, default_value_resolve_context)

                    if original_value is not None:
                        break

                item_to_add = {
                    "key": setting_key,
                    "label": label,
                    "user_value": str(user_changes.getProperty(setting_key, "value", default_value_resolve_context)),
                    "original_value": str(original_value),
                    "extruder": "",
                    "category": category_label,
                }

                if stack != global_stack:
                    item_to_add["extruder"] = stack.getName()

                if category_label not in item_dict:
                    item_dict[category_label] = []
                item_dict[category_label].append(item_to_add)
        for each_item_list in item_dict.values():
            item_list += each_item_list
        self.setItems(item_list)

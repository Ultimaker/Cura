# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.EmptyInstanceContainer import empty_container
import copy

empty_definition_changes_container = copy.deepcopy(empty_container)
empty_definition_changes_container.setMetaDataEntry("id", "empty_definition_changes")
empty_definition_changes_container.setMetaDataEntry("type", "definition_changes")

empty_variant_container = copy.deepcopy(empty_container)
empty_variant_container.setMetaDataEntry("id", "empty_variant")
empty_variant_container.setMetaDataEntry("type", "variant")

empty_material_container = copy.deepcopy(empty_container)
empty_material_container.setMetaDataEntry("id", "empty_material")
empty_material_container.setMetaDataEntry("type", "material")

empty_quality_container = copy.deepcopy(empty_container)
empty_quality_container.setMetaDataEntry("id", "empty_quality")
empty_quality_container.setName("Not Supported")
empty_quality_container.setMetaDataEntry("quality_type", "not_supported")
empty_quality_container.setMetaDataEntry("type", "quality")
empty_quality_container.setMetaDataEntry("supported", False)

empty_quality_changes_container = copy.deepcopy(empty_container)
empty_quality_changes_container.setMetaDataEntry("id", "empty_quality_changes")
empty_quality_changes_container.setMetaDataEntry("type", "quality_changes")
empty_quality_changes_container.setMetaDataEntry("quality_type", "not_supported")

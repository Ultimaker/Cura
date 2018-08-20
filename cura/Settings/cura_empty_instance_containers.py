# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy

from UM.Settings.constant_instance_containers import EMPTY_CONTAINER_ID, empty_container


# Empty definition changes
EMPTY_DEFINITION_CHANGES_CONTAINER_ID = "empty_definition_changes"
empty_definition_changes_container = copy.deepcopy(empty_container)
empty_definition_changes_container.setMetaDataEntry("id", EMPTY_DEFINITION_CHANGES_CONTAINER_ID)
empty_definition_changes_container.setMetaDataEntry("type", "definition_changes")

# Empty variant
EMPTY_VARIANT_CONTAINER_ID = "empty_variant"
empty_variant_container = copy.deepcopy(empty_container)
empty_variant_container.setMetaDataEntry("id", EMPTY_VARIANT_CONTAINER_ID)
empty_variant_container.setMetaDataEntry("type", "variant")

# Empty material
EMPTY_MATERIAL_CONTAINER_ID = "empty_material"
empty_material_container = copy.deepcopy(empty_container)
empty_material_container.setMetaDataEntry("id", EMPTY_MATERIAL_CONTAINER_ID)
empty_material_container.setMetaDataEntry("type", "material")

# Empty quality
EMPTY_QUALITY_CONTAINER_ID = "empty_quality"
empty_quality_container = copy.deepcopy(empty_container)
empty_quality_container.setMetaDataEntry("id", EMPTY_QUALITY_CONTAINER_ID)
empty_quality_container.setName("Not Supported")
empty_quality_container.setMetaDataEntry("quality_type", "not_supported")
empty_quality_container.setMetaDataEntry("type", "quality")
empty_quality_container.setMetaDataEntry("supported", False)

# Empty quality changes
EMPTY_QUALITY_CHANGES_CONTAINER_ID = "empty_quality_changes"
empty_quality_changes_container = copy.deepcopy(empty_container)
empty_quality_changes_container.setMetaDataEntry("id", EMPTY_QUALITY_CHANGES_CONTAINER_ID)
empty_quality_changes_container.setMetaDataEntry("type", "quality_changes")
empty_quality_changes_container.setMetaDataEntry("quality_type", "not_supported")


__all__ = ["EMPTY_CONTAINER_ID",
           "empty_container",  # For convenience
           "EMPTY_DEFINITION_CHANGES_CONTAINER_ID",
           "empty_definition_changes_container",
           "EMPTY_VARIANT_CONTAINER_ID",
           "empty_variant_container",
           "EMPTY_MATERIAL_CONTAINER_ID",
           "empty_material_container",
           "EMPTY_QUALITY_CHANGES_CONTAINER_ID",
           "empty_quality_changes_container",
           "EMPTY_QUALITY_CONTAINER_ID",
           "empty_quality_container"
           ]

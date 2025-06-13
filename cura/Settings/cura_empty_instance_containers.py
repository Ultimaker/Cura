# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy

from UM.Settings.constant_instance_containers import EMPTY_CONTAINER_ID, empty_container
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


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
empty_material_container.setMetaDataEntry("base_file", "empty_material")
empty_material_container.setMetaDataEntry("GUID", "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF")
empty_material_container.setMetaDataEntry("material", "empty")
empty_material_container.setMetaDataEntry("brand", "empty_brand")

# Empty quality
EMPTY_QUALITY_CONTAINER_ID = "empty_quality"
empty_quality_container = copy.deepcopy(empty_container)
empty_quality_container.setMetaDataEntry("id", EMPTY_QUALITY_CONTAINER_ID)
empty_quality_container.setName(catalog.i18nc("@info:not supported profile", "Not supported"))
empty_quality_container.setMetaDataEntry("quality_type", "not_supported")
empty_quality_container.setMetaDataEntry("type", "quality")
empty_quality_container.setMetaDataEntry("supported", False)

# Empty quality changes
EMPTY_QUALITY_CHANGES_CONTAINER_ID = "empty_quality_changes"
empty_quality_changes_container = copy.deepcopy(empty_container)
empty_quality_changes_container.setMetaDataEntry("id", EMPTY_QUALITY_CHANGES_CONTAINER_ID)
empty_quality_changes_container.setMetaDataEntry("type", "quality_changes")
empty_quality_changes_container.setMetaDataEntry("quality_type", "not_supported")
empty_quality_changes_container.setMetaDataEntry("intent_category", "not_supported")

# Empty intent
EMPTY_INTENT_CONTAINER_ID = "empty_intent"
empty_intent_container = copy.deepcopy(empty_container)
empty_intent_container.setMetaDataEntry("id", EMPTY_INTENT_CONTAINER_ID)
empty_intent_container.setMetaDataEntry("type", "intent")
empty_intent_container.setMetaDataEntry("intent_category", "default")
empty_intent_container.setName(catalog.i18nc("@info:No intent profile selected", "Default"))


# All empty container IDs set
ALL_EMPTY_CONTAINER_ID_SET = {
    EMPTY_CONTAINER_ID,
    EMPTY_DEFINITION_CHANGES_CONTAINER_ID,
    EMPTY_VARIANT_CONTAINER_ID,
    EMPTY_MATERIAL_CONTAINER_ID,
    EMPTY_QUALITY_CONTAINER_ID,
    EMPTY_QUALITY_CHANGES_CONTAINER_ID,
    EMPTY_INTENT_CONTAINER_ID
}


# Convenience function to check if a container ID represents an empty container.
def isEmptyContainer(container_id: str) -> bool:
    return container_id in ALL_EMPTY_CONTAINER_ID_SET


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
           "empty_quality_container",
           "ALL_EMPTY_CONTAINER_ID_SET",
           "isEmptyContainer",
           "EMPTY_INTENT_CONTAINER_ID",
           "empty_intent_container"
           ]

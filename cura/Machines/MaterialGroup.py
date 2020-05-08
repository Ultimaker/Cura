# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from cura.Machines.MaterialNode import MaterialNode


class MaterialGroup:
    """A MaterialGroup represents a group of material InstanceContainers that are derived from a single material profile.
    
    The main InstanceContainer which has the ID of the material profile file name is called the "root_material". For
    example: "generic_abs" is the root material (ID) of "generic_abs_ultimaker3" and "generic_abs_ultimaker3_AA_0.4",
    and "generic_abs_ultimaker3" and "generic_abs_ultimaker3_AA_0.4" are derived materials of "generic_abs".
    
    Using "generic_abs" as an example, the MaterialGroup for "generic_abs" will contain the following information:
        - name: "generic_abs", root_material_id
        - root_material_node: MaterialNode of "generic_abs"
        - derived_material_node_list: A list of MaterialNodes that are derived from "generic_abs", so
        "generic_abs_ultimaker3", "generic_abs_ultimaker3_AA_0.4", etc.
    
    """

    __slots__ = ("name", "is_read_only", "root_material_node", "derived_material_node_list")

    def __init__(self, name: str, root_material_node: "MaterialNode") -> None:
        self.name = name
        self.is_read_only = False
        self.root_material_node = root_material_node  # type: MaterialNode
        self.derived_material_node_list = []  # type: List[MaterialNode]

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.name)

from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel
from ...Models import BaseModel


##  Class representing a cloud cluster printer configuration
class CloudClusterPrinterConfigurationMaterial(BaseModel):
    def __init__(self, **kwargs) -> None:
        self.guid = None  # type: str
        self.brand = None  # type: str
        self.color = None  # type: str
        self.material = None  # type: str
        super().__init__(**kwargs)

    ## Creates a material output model based on this cloud printer material.
    def createOutputModel(self) -> MaterialOutputModel:
        material_manager = CuraApplication.getInstance().getMaterialManager()
        material_group_list = material_manager.getMaterialGroupListByGUID(self.guid) or []

        # Sort the material groups by "is_read_only = True" first, and then the name alphabetically.
        read_only_material_group_list = list(filter(lambda x: x.is_read_only, material_group_list))
        non_read_only_material_group_list = list(filter(lambda x: not x.is_read_only, material_group_list))
        material_group = None
        if read_only_material_group_list:
            read_only_material_group_list = sorted(read_only_material_group_list, key = lambda x: x.name)
            material_group = read_only_material_group_list[0]
        elif non_read_only_material_group_list:
            non_read_only_material_group_list = sorted(non_read_only_material_group_list, key = lambda x: x.name)
            material_group = non_read_only_material_group_list[0]

        if material_group:
            container = material_group.root_material_node.getContainer()
            color = container.getMetaDataEntry("color_code")
            brand = container.getMetaDataEntry("brand")
            material_type = container.getMetaDataEntry("material")
            name = container.getName()
        else:
            Logger.log("w", "Unable to find material with guid {guid}. Using data as provided by cluster"
                       .format(guid = self.guid))
            color = self.color
            brand = self.brand
            material_type = self.material
            name = "Empty" if self.material == "empty" else "Unknown"

        return MaterialOutputModel(guid = self.guid, type = material_type, brand = brand, color = color, name = name)

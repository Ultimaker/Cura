from cura.CuraApplication import CuraApplication
from cura.Settings.GlobalStack import GlobalStack
#from cura.Utils.Bcn3dExcludeInstances import removeNonExcludedInstances
from typing import Optional
from UM.Logger import Logger
from cura import ApplicationMetadata

class BCN3DApplication(CuraApplication):
    def __init__(self, *args, **kwargs) -> None:
        Logger.info(f"Init BCN3DApplication")
        #super().__init__(self, **kwargs) # esta linea provoca exit
        super().__init__(name = ApplicationMetadata.CuraAppName,
                        app_display_name = ApplicationMetadata.CuraAppDisplayName,
                        version = ApplicationMetadata.CuraVersion if not ApplicationMetadata.IsAlternateVersion else ApplicationMetadata.CuraBuildType,
                        api_version = ApplicationMetadata.CuraSDKVersion,
                        build_type = ApplicationMetadata.CuraBuildType,
                        is_debug_mode = ApplicationMetadata.CuraDebugMode,
                        tray_icon_name = "cura-icon-32.png" if not ApplicationMetadata.IsAlternateVersion else "cura-icon-32_wip.png",
                        **kwargs)

        #self.default_theme = "stratos"
        
        # Save the print mode to apply it when meshes have been properly loaded
        #self._print_mode_to_load = "singleT0"


    def closeApplication(self) -> None:
        Logger.log("i", " BCN3DApplication Close application")
        #self._global_container_stack.setProperty("print_mode", "value", "singleT0")
        #super().__init__()


    def setGlobalContainerStack(self, stack: Optional["GlobalStack"]) -> None:
        print("***** BCN3DApplication  setGlobalContainerStack start *****")
        self.extractAndSavePrintMode(stack)
        super().setGlobalContainerStack(stack)
        print("***** BCN3DApplication setGlobalContainerStack done *****")
    
    def groupSelected(self) -> None:
        print("***** BCN3DApplication  groupSelected *****")

    #def discardOrKeepProfileChangesClosed(self, option: str) -> None:
    #    global_stack = self.getGlobalContainerStack()
    #    if option == "discard":
    #        for extruder in global_stack.extruderList:
    #            removeNonExcludedInstances(extruder.userChanges)
    #        removeNonExcludedInstances(global_stack.userChanges)

    #    # if the user decided to keep settings then the user settings should be re-calculated and validated for errors
    #    # before slicing. To ensure that slicer uses right settings values
    #    elif option == "keep":
    #        for extruder in global_stack.extruderList:
    #            extruder.userChanges.update()
    #        global_stack.userChanges.update()


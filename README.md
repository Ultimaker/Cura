# MachineSettingsAction
Cura plugin which provides a way to modify printer settings (build volume, nozzle size, start/end gcode) from within Cura.

Installation
----
- Make sure your Cura version is 2.2 or newer
- Download or clone the repository into [Cura installation folder]/plugins/MachineSettingsAction

How to use
----
After adding a machine, go to "Manage Printers...", make sure your printer is active and select "Machine Settings"

Pro-tip: if you add a generic profile to the machine definitions and add ["MachineSettingsAction"] as a first_start_action, you get a nice solution to the "my printer is not listed" problem.

*resources/definitions/generic_fdm.def.json*
```
{
    "version": 2,
    "name": "Generic FDM printer",
    "inherits": "fdmprinter",
    "metadata": {
        "visible": true,
        "author": "Ultimaker",
        "manufacturer": "Generic",
        "category": "Generic",
        "file_formats": "text/x-gcode",
        "has_materials": true,
        "preferred_material": "*pla*",
        "first_start_actions": ["MachineSettingsAction"]
    }
}
```

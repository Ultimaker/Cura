---
name: settings-definitions
description: Find and interpret Cura settings when adding, changing or reviewing Cura settings reads, units, limits, defaults or settings ownership.
---

# Cura settings definitions

Use this skill when working on settings, especially when their meaning, units, limits, dependencies or settings scope is unclear.

A "setting" in Cura always refers to the print settings that are to be customized for every print, depending on the used printer, material, model and user preferences. Those settings are critical to:
* Define the specific characteristics of a printer model
* Ensure a good print quality
* Allow the user to customize the filament usage and print time

Each setting defines a value that is set by the Cura front-end, depending on the context of the print, and the final values are sent to the slicing engine (CuraEngine) where they are applied.

## Authoritative references

Settings definitions are maintained in the public **Ultimaker/Cura** repository:

- Base printer settings: https://github.com/Ultimaker/Cura/blob/main/resources/definitions/fdmprinter.def.json
- Raw base definitions: https://raw.githubusercontent.com/Ultimaker/Cura/main/resources/definitions/fdmprinter.def.json
- Base extruder settings: https://github.com/Ultimaker/Cura/blob/main/resources/definitions/fdmextruder.def.json
- Raw base extruder definitions: https://raw.githubusercontent.com/Ultimaker/Cura/main/resources/definitions/fdmextruder.def.json
- Setting Properties documentation: https://github.com/Ultimaker/Cura/wiki/Setting-Properties
- Raw wiki fallback: https://raw.githubusercontent.com/wiki/Ultimaker/Cura/Setting-Properties.md

Read the Setting Properties documentation alongside the definitions. Use the Cura revision relevant to the task. If access fails, notify the user and ask for the relevant definitions instead of guessing.

Use only these two base definition files for settings guidance, not printer-specific profiles.

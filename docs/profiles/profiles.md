Profiles
====
Cura's profile system is very advanced and has gotten pretty complex. This chapter is an attempt to document how it is structured.

Index
----
The following pages describe the profile and setting system of Cura:
* [Container Stacks](container_stacks.md): Which profiles can be swapped out and how they are ordered when evaluating a setting.
* [Setting Properties](setting_properties.md): What properties can each setting have?

Glossary
----
The terminology for these profiles is not always obvious. Here is a glossary of the terms that we'll use in this chapter.
* **Profile:** Either an *instance container* or a *definition container*.
* **Definition container:** Profile that's stored as .def.json file, defining new settings and all of their properties. In Cura these represent printer models and extruder trains.
* **Instance container:** Profile that's stored as .inst.cfg file or .xml.fdm_material file, which override some setting values. In Cura these represent the other profiles.
* **[Container] stack:** A list of profiles, with one definition container at the bottom and instance containers for the rest. All settings are defined in the definition container. The rest of the profiles each specify a set of value overrides. The profiles at the top always override the profiles at the bottom.
* **Machine instance:** An instance of a printer that the user has added. The list of all machine instances is shown in a drop-down in Cura's interface.
* **Material:** A type of filament that's being sold by a vendor as a product.
* **Filament spool:** A single spool of material.
* **Quality profile:** A profile that is one of the options when the user selects which quality level they want to print with.
* **Intent profile:** A profile that is one of the options when the user selects what his intent is.
* **Custom profile:** A user-made profile that is stored when the user selects to "create a profile from the current settings/overrides".
* **Quality-changes profile:** Alternative name for *custom profile*. This name is used in the code more often, but it's a bit misleading so this documentation prefers the term "custom profile".
* **User profile:** A profile containing the settings that the user has changed, but not yet saved to a profile.
* **Variant profile:** A profile containing some overrides that allow the user to select variants of the definition. As of this writing this is only used for the nozzles.
* **Quality level:** A measure of quality where the user can select from, for instance "normal", "fast", "high". When selecting a quality level, Cura will select a matching quality profile for each extruder.
* **Quality type:** Alternative name for *quality level*. This name is used in the code more often, but this documentation prefers the term "quality level".
* **Inheritance function:** A function through which the `value` of a setting is calculated. This may depend on other settings.
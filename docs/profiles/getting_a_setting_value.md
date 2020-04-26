Getting a Setting Value
====
How Cura gets a setting's value is a complex endeavour that requires some explanation. The `value` property gets special treatment for this because there are a few other properties that influence the value. In this page we explain the algorithm to getting a setting value.

This page explains all possible cases for a setting, but not all of them may apply. For instance, a global setting will not evaluate the per-object settings to get its value. Exceptions to the rules for other types of settings will be written down.

Per Object Settings
----
Per-object settings, which are added to an object using the per-object settings tool, will always prevail over other setting values. They are not evaluated with the rest of the settings system because Cura's front-end doesn't need to send all setting values for all objects to CuraEngine separately. It only sends over the per-object settings that get overridden. CuraEngine then evaluates settings that can be changed per-object using the list of settings for that object but if the object doesn't have the setting attached falls back on the settings in the object's extruder. Refer to the [CuraEngine](#CuraEngine) chapter to see how this works.

Settings where the `settable_per_mesh` property is false will not be shown in Cura's interface in the list of available settings in the per-object settings panel. They cannot be adjusted per object then. CuraEngine will also not evaluate those settings for each object separately. There is (or should always be) a good reason why each of these settings are not evaluated per object: Simply because CuraEngine is not processing one particular mesh at that moment. For instance, when writing the move to change to the next layer, CuraEngine hasn't processed any of the meshes on that layer yet and so the layer change movement speed, or indeed the layer height, can't change for each object.

The per-object settings are stored in a separate container stack that is particular to the object. The container stack is added to the object via a scene decorator. It has just a single container in it, which contains all of the settings that the user changed.

Resolve
----
If the setting is not listed in the per-object settings, it needs to be evaluated from the main settings list. However before evaluating it from a particular extruder, Cura will check if the setting has the `resolve` property. If it does, it returns the output of the `resolve` property and that's everything.

The `resolve` property is intended for settings which are global in nature, but still need to be influenced by extruder-specific settings. A good example is the Build Plate Temperature, which is very dependent on the material(s) used by the printer, but there can only be a single bed temperature at a time.

Cura will simply evaluate the `resolve` setting if present, which is an arbitrary Python expression, and return its result as the setting's value. However typically the `resolve` property is a function that takes the values of this setting for all extruders in use and then computes a result based on those. There is a built-in function for that called `extruderValues()`, which returns a list of setting values, one for each extruder. The function can then for instance take the average of those. In the case of the build plate temperature it will take the highest of those. In the case of the adhesion type it will choose "raft" if any extruder uses a raft, or "brim" as second choice, "skirt" as third choice and "none" only if all extruders use "none". Each setting with a `resolve` property has its own way of resolving the setting. The `extruderValues()` function continues with the algorithm as written below, but repeats it for each extruder.

Limit To Extruder
----
If a setting is evaluated from a particular extruder stack, it normally gets evaluated from the extruder that the object is assigned to. However there are some exceptions. Some groups of settings belong to a particular "extruder setting", like the Infill Extruder setting, or the Support Extruder setting. Which extruder a setting belongs to is stored in the `limit_to_extruder` property. Settings which have their `limit_to_extruder` property set to `adhesion_extruder_nr`, for instance, belong to the build plate adhesion settings.

If the `limit_to_extruder` property evaluates to a positive number, instead of getting the setting from the object's extruder it will be obtained from the extruder written in the `limit_to_extruder` property. So even if an object is set to be printed with extruder 0, if the infill extruder is set to extruder 1 any infill setting will be obtained from extruder 1. If `limit_to_extruder` is negative (in particular -1, which is the default), then the setting will be obtained from the object's own extruder.

This property is communicated to CuraEngine separately. CuraEngine makes sure that the setting is evaluated from the correct extruder. Refer to the [CuraEngine](#CuraEngine) chapter to see how this works.
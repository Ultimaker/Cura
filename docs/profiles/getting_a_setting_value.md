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

Evaluating a Stack
----
After the resolve and limit to extruder properties have been checked, the setting value needs to be evaluated from an extruder stack.

This is explained in more detail in the [Container Stacks](container_stacks.md) documentation. In brief, Cura will check the highest container in the extruder stack first to see whether that container overrides the setting. If it does, it returns that as the setting value. Otherwise, it checks the second container on the stack to see if that one overrides it. If it does it returns that value, and otherwise it checks the third container, and so on. If a setting is not overridden by any container in the extruder stack, it continues downward in the global stack. If it is also not overridden there, it eventually arrives at the definition in the bottom of the global stack.

Evaluating a Definition
----
If the evaluation for a setting reaches the last entry of the global stack, its definition, a few more things can happen.

Definition containers have an inheritance structure. For instance, the `ultimaker3` definition container specifies in its metadata that it inherits from `ultimaker`, which in turn inherits from `fdmprinter`. So again here, when evaluating a property from the `ultimaker3` definition it will first look to see if the property is overridden by the `ultimaker3` definition itself, and otherwise refer on to the `ultimaker` definition or otherwise finally to the `fdmprinter` definition. `fdmprinter` is the last line of defence, and it contains *all* properties for *all* settings.

But even in `fdmprinter`, not all settings have a `value` property. It is not a required property. If the setting doesn't have a `value` property, the `default_value` property is returned, which is a required property. The distinction between `value` and `default_value` is made in order to allow CuraEngine to load a definition file as well when running from the command line (a debugging technique for CuraEngine). It then won't have all of the correct setting values but it at least doesn't need to evaluate all of the Python expressions and you'll be able to make some debugging slices.

Evaluating a Value Property
----
The `value` property may contain a formula, which is an arbitrary Python expression that will be executed by Cura to arrive at a setting value. All containers may set the `value` property. Instance containers can only set the `value`, while definitions can set all properties.

While the value could be any sort of formula, some functions of Python are restricted for security reasons. Since Cura 4.6, profiles are no longer a "trusted" resource and are therefore subject to heavy restrictions. It can use Python's built in mathematical functions and list functions as well as a few basic other ones, but things like writing to a file are prohibited.

There are also a few extra things that can be used in these expressions:
* Any setting key can be used as a variable that contains the setting's value.
* As explained before, `extruderValues(key)` is a function that returns a list of setting values for a particular setting for all used extruders.
* The function `extruderValue(extruder, key)` will evaluate a particular setting for a particular extruder.
* The function `resolveOrValue(key)` will perform the full setting evaluation as described in this document for the current context (so if this setting is being evaluated for the second extruder it would perform it as if coming from the second extruder).
* The function `defaultExtruderPosition()` will get the first extruder that is not disabled. For instance, if a printer has three extruders but the first is disabled, this would return `1` to indicate the second extruder (0-indexed).
* The function `valueFromContainer(key, index)` will get a setting value from the global stack, but skip the first few containers in that stack. It will skip until it reaches a particular index in the container stack.
* The function `valueFromExtruderContainer(key, index)` will get a setting value from the current extruder stack, but skip the first few containers in that stack. It will skip until it reaches a particular index in the container stack.

CuraEngine
----
When starting a slice, Cura will send the scene to CuraEngine and with each model send over the per-object settings that belong to it. It also sends all setting values over, as evaluated from each extruder and from the global stack, and sends the `limit_to_extruder` property along as well. CuraEngine stores this and then starts its slicing process. CuraEngine also has a hierarchical structure for its settings with fallbacks. This is explained in detail in [the documentation of CuraEngine](https://github.com/Ultimaker/CuraEngine/blob/master/docs/settings.md) and shortly again here.

Each model gets a setting container assigned. The per-object settings are stored in those. The fallback for this container is set to be the extruder with which the object is printed. The extruder uses the current *mesh group* as fallback (which is a concept that Cura's front-end doesn't have). Each mesh group uses the global settings container as fallback.

During the slicing process CuraEngine will evaluate the settings from its current context as it goes. For instance, when processing the walls for a particular mesh, it will request the Outer Wall Line Width setting from the settings container of that mesh. When it's not processing a particular mesh but for instance the travel moves between two meshes, it uses the currently applicable extruder. So this business logic defines actually how a setting can be configured per mesh, per extruder or only globally. The `settable_per_extruder`, and related properties of settings are only used in the front-end to determine how the settings are shown to the user.
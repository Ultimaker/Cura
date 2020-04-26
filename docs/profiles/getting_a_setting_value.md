Getting a Setting Value
====
How Cura gets a setting's value is a complex endeavour that requires some explanation. The `value` property gets special treatment for this because there are a few other properties that influence the value. In this page we explain the algorithm to getting a setting value.

This page explains all possible cases for a setting, but not all of them may apply. For instance, a global setting will not evaluate the per-object settings to get its value. Exceptions to the rules for other types of settings will be written down.

Per Object Settings
----
Per-object settings, which are added to an object using the per-object settings tool, will always prevail over other setting values. They are not evaluated with the rest of the settings system because Cura's front-end doesn't need to send all setting values for all objects to CuraEngine separately. It only sends over the per-object settings that get overridden. CuraEngine then evaluates settings that can be changed per-object using the list of settings for that object but if the object doesn't have the setting attached falls back on the settings in the object's extruder. Refer to the [CuraEngine](#CuraEngine) chapter to see how this works.
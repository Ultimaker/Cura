Profiles
====
Cura's profile system is very advanced and has gotten pretty complex. This chapter is an attempt to document how it is structured.

Glossary
----
The terminology for these profiles is not always obvious. Here is a glossary of the terms that we'll use in this chapter.
* **Profile:** Either an *instance container* or a *definition container*.
* **Definition container:** Profile that's stored as .def.json file, defining new settings and all of their properties. In Cura these represent printer models and extruder trains.
* **Instance container:** Profile that's stored as .inst.cfg file or .xml.fdm_material file, which override some setting values. In Cura these represent the other profiles.
* **[Container] Stack:** A list of profiles, with one definition container at the bottom and instance containers for the rest. All settings are defined in the definition container. The rest of the profiles each specify a set of value overrides. The profiles at the top always override the profiles at the bottom.
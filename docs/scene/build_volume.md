Build Volume
====
The build volume is a scene node. This node gets placed somewhere in the scene. This is a specialised scene node that draws the build volume and all of its bits and pieces.

Volume bounds
----
The build volume draws a cube (for rectangular build plates) that represents the printable build volume. This outline is drawn with a blue line. To render this, the Build Volume scene node generates a cube and instructs OpenGL to draw a wireframe of this cube. This way the wireframe is always a single pixel wide regardless of view distance. This cube is automatically resized when the relevant settings change, like the width, height and depth of the printer, the shape of the build plate, the Print Sequence or the gantry height.

The build volume also draws a grid underneath the build volume. The grid features 1cm lines which allows the user to roughly estimate how big its print is or the distance between prints. It also features a finer 1mm line pattern within that grid. The grid is drawn as a single quad. This quad is then sent to the graphical card with a specialised shader which draws the grid pattern.

For elliptical build plates, the volume bounds are drawn as two circles, one at the top and one at the bottom of the available height. The build plate grid is drawn as a tesselated circle, but with the same shader.

Disallowed areas
----
The build volume also calculates and draws the disallowed areas. These are drawn as a grey shadow. The point of these disallowed areas is to denote the areas where the user is not allowed to place any objects. The reason to forbid placing an object can be a lot of things.

One disallowed area that is always present is the border around the build volume. This border is there to prevent the nozzle from going outside of the bounds of the build volume. For instance, if you were to print an object with a brim of 8mm, you won't be able to place that object closer than 8mm to the edge of the build volume. Doing so would draw part of the brim outside of the build volume. The width of these disallowed areas depends on a bunch of things. Most commonly the build plate adhesion setting or the Avoid Distance setting is the culprit. However this border is also affected by the draft shield, ooze shield and Support Horizontal Expansion, among others.

Another disallowed area stems from the distance between the nozzles for some multi-extrusion printers. The total build volume in Cura is normally the volume that can be reached by either nozzle. However for every extruder that your print uses, the build volume will be shrunk to the intersecting area that all used nozzles can reach. This is done by adding disallowed areas near the border. For instance, if you have two extruders with 18mm X distance between them, and your print uses only the left extruder, there will be an extra border of 18mm on the right hand side of the printer, because the left nozzle can't reach that far to the right. If you then use both extruders, there will be an 18mm border on both sides.

There are also disallowed areas for features that are printed. There are as of this writing two such disallowed areas: The prime tower and the prime blob. You can't print an object on those locations since they would intersect with the printed feature.

Then there are disallowed areas imposed by the current printer. Some printers have things in the way of your print, such as clips that hold the build plate down, or cameras, switching bays or wiping brushes. These are encoded in the `machine_disallowed_areas` and `nozzle_disallowed_areas` settings, as polygons. The difference between these two settings is that one is intended to describe where the print head is not allowed to move. The other is intended to describe where the currently active nozzle is not allowed to move. This distinction is meant to allow inactive nozzles to move over things like build plate clips or stickers, which can slide underneath an inactive nozzle.

Finally, there are disallowed areas imposed by other objects that you want to print. Each object and group has an associated Convex Hull Node, which denotes the volume that the object is going to be taking up while printing. This convex hull is projected down to the build plate and determines there the volume that the object is going to occupy.

Each type of disallowed area is affected by certain settings. The border around the build volume, for instance, is affected by the brim, but the disallowed areas for printed objects are not. This is because the brim could go outside of the build volume but the brim can't hit any other objects. If the brim comes too close to other objects, it merges with the brim of those objects. As such, generating each type of disallowed area requires specialised business logic to determine how the setting affects the disallowed area. It needs to take the highest of two settings sometimes, or it needs to sum them together, multiplying a certain line width by an accompanying line count setting, and so on. All this logic is implemented in the BuildVolume class.
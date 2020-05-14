Scene
====
The 3D scene in Cura is designed as a [Scene Graph](https://en.wikipedia.org/wiki/Scene_graph), which is common in many 3D graphics applications. The scene graph of Cura is usually very flat, but has the possibility to have nested objects which inherit transformations from each other.

Scene Graph
----
Cura's scene graph is a mere tree data structure. This tree contains all scene nodes, which represent the objects in the 3D scene.

The main idea behind the scene tree is that each scene node has a transformation applied to it. The scene nodes can be nested beneath other scene nodes. The transformation of the parents is then also applied to the children. This way you can have scene nodes grouped together and transform the group as a whole. Since the transformations are all linear, this ensures that the elements of this group stay in the same relative position and orientation. It will look as if the whole group is a single object. This idea is very common for games where objects are often composed of multiple 3D models but need to move together as a whole. For Cura it is used to group objects together and to transform the collision area correctly.

A Typical Scene
----
Cura's scene has a few nodes that are always present, and a few nodes that are repeated for every object that the user loads onto their build plate. To give an idea of how a scene normally looks, this is an overview of a typical scene tree for Cura.

* Root
  * Camera
  * [Build volume](build_volume.md)
    * Platform
  * Object 1
  * Group 1
    * Object 2
    * Object 3
  * Object 1 convex hull node
  * Object 2 convex hull node
  * Object 3 convex hull node
  * Group 1 convex hull node
# Operations and the OperationStack

Cura supports an operation stack. The `OperationStack` class maintains a history of the operations performed in Cura, which allows for undo and redo actions. Every operation registers itself in the stack. The OperationStuck supports the following functions:

  * `push(operation)`: Pushes an operation in the stack and applies the operation. This function is called when an operation pushes itself in the stack.
  * `undo()`: Reverses the actions performed by the last operation and reduces the current index of the stack.
  * `redo()`: Applies the actions performed by the next operation in the stack and increments the current index of the stack.
  * `getOperations()`: Returns a list of all the operations that are currently inside the OperationStack
  * `canUndo()`: Indicates whether the index of the operation stack has reached the bottom of the stack, which means that there are no more operations to be undone.
  * `canRedo()`: Indicates whether the index of the operation stack has reached the top of the stack, which means that there are no more operations to be redone.

**Note 1:** When consecutive operations are performed very quickly after each other, they are merged together at the top of the stack. This action ensures that these minor operation will be undone with one Undo keystroke (e.g. when moving the object around and you press and release the left mouse button really fast, it is considered as one move operation).

**Note 2:** When an operation is pushed in the middle of the stack, all operations above it are removed from the stack. This ensures that there won't be any "history branches" created. 

### Operations

Every action that happens in the scene and affects one or multiple models is associated with a subclass of the `Operation` class and is it added to the `OperationStack`. The subclassed operations that can be found in Cura (excluding the ones from downloadable plugins) are the following:

  * [GroupedOperation](#groupedoperation)
  * [AddSceneNodeOperation](#addscenenodeoperation)
  * [RemoveSceneNodeOperation](#removescenenodeoperation)
  * [SetParentOperation](#setparentoperation)
  * [SetTransformOperation](#settransformoperation)
  * [SetObjectExtruderOperation](#setobjectextruderoperation)
  * [GravityOperation](#gravityoperation)
  * [PlatformPhysicsOperation](#platformphysicsoperation)
  * [TranslateOperation](#translateoperation)
  * [ScaleOperation](#scaleoperation)
  * [RotateOperation](#rotateoperation)
  * [MirrorOperation](#mirroroperation)
  * [LayFlatOperation](#layflatoperation)
  * [SetBuildPlateNumberOperation]()

### GroupedOperation

The `GroupedOperation` is an operation that groups several other operations together. The intent of this operation is to hide an underlying chain of operations from the user if they correspond to only one interaction with the user, such as an operation applied to multiple scene nodes or a re-arrangement of multiple items in the scene.

Once a `GroupedOperation` is pushed into the stack, it applies all of its children operations in one go. Similarly, when it is undone, it reverses all its children operations at once.


### AddSceneNodeOperation

The `AddSceneNodeOperation` is added to the stack whenever a mesh is loaded inside the `Scene`, either by a `FileReader` or by inserting a [Support Blocker](tools.md#supporteraser-tool) in an object.

### RemoveSceneNodeOperation

The `RemoveSceneNodeOperation` is added to the stack whenever a mesh is removed from the Scene by the user or when the user requests to clear the build plate (_Ctrl+D_).

### SetParentOperation

The `SetParentOperation` changes the parent of a node. It is primarily used when grouping (the group node is set as the nodes' parent) and ungrouping (the group's children's parent is set to the group's parent before the group node is deleted), or when a SupportEraser node is added to the scene (to set the selected object as the Eraser's parent).

### SetTransformOperation

The `SetTransformOperation` translates, rotates, and scales a node all at once. This operation accepts a transformation matrix, an orientation matrix, and a scale matrix, and it is used by the _"Reset All Model Positions"_ and _"Reset All Model Transformations"_ options in the right-click (context) menu.

### SetObjectExtruderOperation

This operation is used to set the extruder with which a certain object should be printed with. It adds a [SettingOverrideDecorator](scene.md#settingoverridedecorator) to the object (if it doesn't have any) and then sets the extruder number via the decoration function `node.callDecoration("setActiveExtruder", extruder_id)`.

### GravityOperation

The `GravityOperation` moves a scene node down to 0 on the y-axis. It is currently used by the _"Lay flat"_ and _"Select face to align to the build plate"_ actions of the `RotationTool` to ensure that the object will end up touching the build plate after the corresponding rotation operations have be done.

### PlatformPhysicsOperation

The `PlatformPhysicsOperation` is generated by the `PlatformPhysics` class and it is associated with the preferences _"Ensure models are kept apart"_ and _"Automatically drop models to the build plate"_. If any of these preferences is set to true, the `PlatformPhysics` class periodically checks to make sure that the two conditions are met and if not, it calculates the move vector for each of the nodes that will satisfy the conditions. 

Once the move vectors have been computed, they are applied to the nodes through consecutive `PlatformPhysicsOperations`, whose job is to use the `translate` function on the nodes. 

**Note:** When there are multiple nodes, multiple `PlatformPhysicsOperations` may be generated (all models may be moved to ensure they are kept apart). These operations eventually get merged together by the `OperationStack` due to the fact that the individual operations are applied very fast one after the other.

### TranslateOperation

The `TranslateOperation` applies a linear transformation on a node, moving the node in the scene. This operation is primarily linked to the [TranslateTool](tools.md#translatetool) but it is also used in other places around Cura, such as arranging objects on the build plate (Ctrl+R) and centering an object to the build plate (via the right-click context menu's _"Center Selected Model"_ option).

When an object is moved using the move tool handles, multiple translate operations are generated to make sure that the object is rendered properly while it is moved. These translate operations are merged together once the user releases the tool handle.

**Note:** Some functionalities may move (translate) nodes without generating a TranslateOperation (such as when a model with is imported from a 3mf into a certain position). This ensures that the moving of the object cannot be accidentally undone by the user.

### ScaleOperation

The `ScaleOperation` scales the selected scene node uniformly or non-uniformly. This operation is primarily generated by the [ScaleTool](tools.md#scaletool).

When an object is scaled using the scale tool handles, multiple scale operations are generated to make sure that the object is rendered properly while it is being resized. These scale operations are merged together once the user releases the tool handle.

**Note:** When the _"Scale extremely small models"_ or the _"Scale large models"_ preferences are enabled the model is scaled when it is inserted into the build plate but it **DOES NOT** generate a `ScaleOperation`. This ensures that Cura doesn't register the scaling as an action that can be undone and the user doesn't accidentally end up with a very big or very small model.


### RotateOperation

The `RotateOperation` rotates the selected scene node(s) according to a given rotation quaternion and, optionally, around a given point. This operation is primarily generated by the [RotationTool](tools.md#rotatetool). It is also used by the arrange algorithm, which may rotate some models to fit them in the build plate.

When an object is rotated using the rotate tool handles, multiple rotate operations are generated to make sure that the object is rendered properly while it is being rotated. These operations are merged together once the user releases the tool handle.

### MirrorOperation

The `MirrorOperation` mirrors the selected object. It is primarily associated with the [MirrorTool](tools.md#mirrortool) and allows for mirroring the object in a certain direction, using the `MirrorToolHandles`. 

The `MirrorOperation` accepts a transformation matrix that should only define values on the diagonal of the matrix, and only the values 1 or -1. It allows for mirroring around the center of the object or around the axis origin. The latter isn't used that often.

### LayFlatOperation

The `LayFlatOperation` computes some orientation to hopefully lay the object flat on the build plate. It is generated by the `layFlat()` function of the [RotateTool](tools.md#rotatetool). Contrary to the other operations, the `LayFlatOperation` is computed in a separate thread through the `LayFlatJob` since it can be quite computationally expensive.


### SetBuildPlateNumberOperation

The `SetBuildPlateNumberOperation` is linked to a legacy feature which allowed the user to have multiple build plates open in Cura at the same time. With this operation it was possible to transfer a node to another build plate through the node's [BuildPlateDecorator](scene.md#buildplatedecorator) by calling the decoration `node.callDecoration("setBuildPlateNumber", new_build_plate_nr)`.

**Note:** Changing the active build plate is a disabled feature in Cura and it is intended to be completely removed (internal ticket: CURA-4975), along with the `SetBuildPlateNumberOperation`.


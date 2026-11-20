# gRPC Protocol shared between Cura front-end and CuraEngine
The protocol is defined in the `Cura.proto` file. The very same files exists in both `Cura/plugins/CuraEngineBackend/protocol/Cura.proto` and `CuraEngine/Cura.proto`, thus when changing any of them, make sure you copy it on the other project.

* In the frontend, the generated protobuf classes are stored in Git for development convenience. Thus every time the `Cura.proto` files changes, it is the responsibility of the developer to re-generate and commit them. In order to do that, a convenience script is provided, but requires the run venv to be setup:

```
source build/generators/virtual_python_env.sh
python ./scripts/update_protobuf_objects.py
```

* On CuraEngine, this is done automatically via CMake at build-time. Thus there is no need to care about re-generating.

# Protocol description
gRPC is designed to send unitary requests between remote objects, opening a new HTTP request for each call. This is too heavy in our case, so the workaround is to declare the following unique service:

```
service CuraEngineCommunication {
  rpc Communicate(stream CuraEngineMessage) returns (stream CuraClientMessage);
}
```

Because the arguments are declared with the `stream` flag, calling this method once will create a long-life communication channel, on which multiple messages can be exchanged in both directions.

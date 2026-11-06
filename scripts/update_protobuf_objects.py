try:
  import grpc_tools.protoc
except ModuleNotFoundError:
  print("Unable to load the grpc_tools module, remember to execute this scrit within the Cura build venv, e.g. 'source build/generators/virtual_python_env.sh'")
  exit(1)

grpc_tools.protoc.main(["protoc", "-I.", "--python_out=.", "--grpc_python_out=.", "plugins/CuraEngineBackend/protocol/Cura.proto"])

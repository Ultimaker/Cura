import importlib.metadata
from . import CuraVersion

CuraVersion.PythonInstalls = {package.metadata['Name']: {'version': package.metadata['Version']} for package in importlib.metadata.distributions()}

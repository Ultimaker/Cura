from UM.Util import parseBool


#
# Gets the machine definition ID that can be used to search for Quality containers that are suitable for the given
# machine. The rule is as follows:
#   1. By default, the machine definition ID for quality container search will be "fdmprinter", which is the generic
#      machine.
#   2. If a machine has its own machine quality (with "has_machine_quality = True"), we should use the given machine's
#      own machine definition ID for quality search.
#      Example: for an Ultimaker 3, the definition ID should be "ultimaker3".
#   3. When condition (2) is met, AND the machine has "quality_definition" defined in its definition file, then the
#      definition ID specified in "quality_definition" should be used.
#      Example: for an Ultimaker 3 Extended, it has "quality_definition = ultimaker3". This means Ultimaker 3 Extended
#               shares the same set of qualities profiles as Ultimaker 3.
#
def getMachineDefinitionIDForQualitySearch(machine: "GlobalStack", default_definition_id: str = "fdmprinter") -> str:
    machine_definition_id = default_definition_id
    if parseBool(machine.getMetaDataEntry("has_machine_quality", False)):
        # Only use the machine's own quality definition ID if this machine has machine quality.
        machine_definition_id = machine.getMetaDataEntry("quality_definition")
        if machine_definition_id is None:
            machine_definition_id = machine.definition.getId()

    return machine_definition_id

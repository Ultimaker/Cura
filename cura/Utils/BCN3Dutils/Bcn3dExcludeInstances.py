
#Exclude changes to instances that will not be taken into consideration.
excludedInstances = ["print_mode"]

#Check if we need hidrate Category label for show in menu
def hidrateCategoryLabel(category_label, item_to_add):
    if item_to_add["key"] not in excludedInstances:
        category_label.append(item_to_add)
    return category_label

#Provide the current number of modified instances from a stack excluding desired ones
def countNonExcludedInstances(stack):
    all_instances = stack.findInstances()
    num_user_settings = 0
    for instance in all_instances:
        if instance.definition.key not in excludedInstances:
                num_user_settings += 1
    return num_user_settings

#Delete all instances except the excluded ones
def removeNonExcludedInstances(userChanges):
    instances = userChanges.findInstances()
    if instances:
        userChanges._instantiateCachedValues()
        for instance in instances:
            if instance.definition.key != "print_mode":
                userChanges.removeInstance(instance.definition.key, postpone_emit=True)
        userChanges.sendPostponedEmits()


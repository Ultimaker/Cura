import nbt

def nested_string(tag, indent_string="  ", indent=0):
    result = ""

    if tag.tagID == nbt.TAG_COMPOUND:
        result += 'TAG_Compound({\n'
        indent += 1
        for key, value in tag.iteritems():
            result += indent_string * indent + '"%s": %s,\n' % (key, nested_string(value, indent_string, indent))
        indent -= 1
        result += indent_string * indent + '})'

    elif tag.tagID == nbt.TAG_LIST:
        result += 'TAG_List([\n'
        indent += 1
        for index, value in enumerate(tag):
            result += indent_string * indent + nested_string(value, indent_string, indent) + ",\n"
        indent -= 1
        result += indent_string * indent + '])'

    else:
        result += "%s(%r)" % (tag.__class__.__name__, tag.value)

    return result



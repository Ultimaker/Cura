import re


def charsInLine(characters, line):
    for c in characters:
        if c not in line:
            return False
    return True

##  Convenience function that finds the value in a line of g-code.
#   When requesting key = x from line "G1 X100" the value 100 is returned.
def getValue(line, key, default=None):
    if not key in line or (';' in line and line.find(key) > line.find(';')):
        return default
    sub_part = line[line.find(key) + 1:]
    m = re.search('^-?[0-9]+\.?[0-9]*', sub_part)
    if m is None:
        return default
    try:
        num = float(m.group(0))
        if num % 1 == 0:
            return int(num)
        else:
            return num
    except:
        return default
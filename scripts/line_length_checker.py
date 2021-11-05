import re
import sys

def getValue(line: str, key: str, default = None):
    """Convenience function that finds the value in a line of g-code.
    When requesting key = x from line "G1 X100" the value 100 is returned.
    """
    if not key in line or (';' in line and line.find(key) > line.find(';')):
        return default
    sub_part = line[line.find(key) + 1:]
    m = re.search('^-?[0-9]+\.?[0-9]*', sub_part)
    if m is None:
        return default
    try:
        return int(m.group(0))
    except ValueError: #Not an integer.
        try:
            return float(m.group(0))
        except ValueError: #Not a number at all.
            return default

def analyse(gcode, distance_to_report, print_layers = False):
    lines_found = 0
    previous_x = 0
    previous_y = 0
    dist_squared = distance_to_report * distance_to_report
    current_layer = 0
    for line in gcode.split("\n"):
        if not line.startswith("G1"):
            if line.startswith(";LAYER:"):
                previous_x = 0
                previous_y = 0
                current_layer += 1
            continue
        current_x = getValue(line, "X")
        current_y = getValue(line, "Y")
        if current_x is None or current_y is None:
            continue
        diff_x = current_x - previous_x
        diff_y = current_y - previous_y
        if diff_x * diff_x + diff_y * diff_y < dist_squared:
            lines_found += 1
            if print_layers:
                print("[!] ", distance_to_report, " layer ", current_layer, " ", previous_x, previous_y)
        previous_y = current_y
        previous_x = current_x
    return lines_found
    
def loadAndPrettyPrint(file_name):
    print(file_name.replace(".gcode",""))
    with open(file_name) as f:
        data = f.read()
    print("| Line length | Num segments |")
    print("| ------------- | ------------- |")
    print("| 1 |", analyse(data, 1), "|")
    print("| 0.5 |", analyse(data, 0.5), "|")
    print("| 0.1 |", analyse(data, 0.1), "|")
    print("| 0.05 |", analyse(data, 0.05), "|")
    print("| 0.01 |", analyse(data, 0.01), "|")
    print("| 0.005 |", analyse(data, 0.005), "|")
    print("| 0.001 |", analyse(data, 0.001), "|")


if __name__ == "__main__":
    if len(sys.argv) != 2 :
        print("Usage: <input g-code>")
        sys.exit(1)
    
    in_filename = sys.argv[1]
    loadAndPrettyPrint(sys.argv[1])

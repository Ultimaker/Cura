import os
import json
# Global Counters

CORRUPTION_COUNTER = []
KEYERROR_COUNTER = []
VALUEERROR_COUNTER = []


def assert_corruption_error():
    assert len(CORRUPTION_COUNTER) == 0


def assert_key_error():
    assert len(KEYERROR_COUNTER) == 0


def assert_value_error():
    assert len(VALUEERROR_COUNTER) == 0


def find_extruder(file, extruder_trains, extruders):
    if len(extruder_trains) == 1:
        if '0' in extruder_trains.keys():
            value = f"{extruder_trains['0']}.def.json"
        else:
            value = f"{extruder_trains['1']}.def.json"
        if value in extruders or value == "fdmextruder.def.json":
            pass
        else:
            VALUEERROR_COUNTER.append(f"No value found for {file} pointing to {value}")
    elif len(extruder_trains) > 1:
        for key, value in extruder_trains.items():
            value = f"{value}.def.json"
            if value in extruders:
                pass
            else:
                VALUEERROR_COUNTER.append(f"No value found for {file} with {value}")
    else:
        raise Exception(f"No extruder train found for {file}")


def find_inheritance(base_path, parent):
    if parent == "fdmprinter":
        return {'0': 'fdmextruder'}

    with open(f"{base_path}/definitions/{parent}.def.json", 'r') as f:
        json_file = json.load(f)

    if "metadata" in json_file.keys() and "machine_extruder_trains" in json_file["metadata"].keys():
        return json_file["metadata"]["machine_extruder_trains"]
    elif "inherits" in json_file.keys():
        return find_inheritance(base_path, json_file["inherits"])
    else:
        KEYERROR_COUNTER.append(f"Could not find the either a parent or extruder train for {parent}")


def printer_definition_checker():
    base_path = os.path.dirname(os.getcwd())
    base_path = os.path.join(base_path, "resources")
    definitions = next(os.walk(f"{base_path}/definitions"), (None, None, []))[2]
    extruders = next(os.walk(f"{base_path}/extruders"), (None, None, []))[2]

    for file in definitions:
        if file in ["fdmprinter.def.json", "fdmextruder.def.json"]:
            continue
        with open(f"{base_path}/definitions/{file}", 'r') as f:
            json_file = json.load(f)

        if "metadata" in json_file.keys() and "machine_extruder_trains" in json_file["metadata"].keys():
            extruder_trains = json_file["metadata"]["machine_extruder_trains"]
        elif "inherits" in json_file.keys():
            extruder_trains = find_inheritance(base_path, json_file["inherits"])
        else:
            CORRUPTION_COUNTER.append(f"{file} is likely to be corrupted please investigate.")

        find_extruder(file, extruder_trains, extruders)


def log_results():
    counters = [VALUEERROR_COUNTER, KEYERROR_COUNTER, CORRUPTION_COUNTER]
    for sublist in counters:
        print(*sublist, sep='\n')


if __name__ == '__main__':
    printer_definition_checker()
    log_results()
    assert_corruption_error()
    assert_value_error()
    assert_key_error()

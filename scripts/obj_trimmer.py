# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import argparse
import os
from typing import Optional, List, TextIO

"""
    Used to reduce the size of obj files used for printer platform models.
    
    Trims trailing 0 from coordinates
    Removes duplicate vertex texture coordinates
    Removes any rows that are not a face, vertex or vertex texture
"""


def process_obj(input_file: str, output_file: str) -> None:
    with open(input_file, "r") as in_obj, open("temp", "w") as temp:
        trim_lines(in_obj, temp)

    with open("temp", "r") as temp, open(output_file, "w") as out_obj:
        merge_duplicate_vt(temp, out_obj)

    os.remove("temp")


def trim_lines(in_obj: TextIO, out_obj: TextIO) -> None:
    for line in in_obj:
        line = trim_line(line)
        if line:
            out_obj.write(line + "\n")


def trim_line(line: str) -> Optional[str]:
    # Discards all rows that are not a vertex ("v"), face ("f") or vertex texture ("vt")
    values = line.split()

    if values[0] == "vt":
        return trim_vertex_texture(values)
    elif values[0] == "f":
        return trim_face(values)
    elif values[0] == "v":
        return trim_vertex(values)

    return


def trim_face(values: List[str]) -> str:
    # Removes face normals (vn)
    # f 15/15/17 15/15/17 14/14/17 -> f 15/15 15/15 14/14
    for i, coordinates in enumerate(values[1:]):
        v, vt = coordinates.split("/")[:2]
        values[i + 1] = v + "/" + vt

    return " ".join(values)


def trim_vertex(values: List[str]) -> str:
    # Removes trailing zeros from vertex coordinates
    # v 0.044000 0.137000 0.123000 -> v 0.044 0.137 0.123
    for i, coordinate in enumerate(values[1:]):
        values[i + 1] = str(float(coordinate))
    return " ".join(values)


def trim_vertex_texture(values: List[str]) -> str:
    # Removes trailing zeros from vertex texture coordinates
    # vt 0.137000 0.123000 -> v 0.137 0.123
    for i, coordinate in enumerate(values[1:]):
        values[i + 1] = str(float(coordinate))
    return " ".join(values)


def merge_duplicate_vt(in_obj, out_obj):
    # Removes duplicate vertex texture ("vt")
    # Points references to all deleted copies in face ("f") to a single vertex texture

    # Maps index of all copies of a vt line to the same index
    vt_index_mapping = {}
    # Maps vt line to index ("vt 0.043 0.137" -> 23)
    vt_to_index = {}

    # .obj file indexes start at 1
    vt_index = 1
    skipped_count = 0

    # First write everything except faces
    for line in in_obj.readlines():
        if line[0] == "f":
            continue

        if line[:2] == "vt":
            if line in vt_to_index.keys():
                # vt with same value has already been written
                # this points the current vt index to the one that has been written
                vt_index_mapping[vt_index] = vt_to_index[line]
                skipped_count += 1
            else:
                # vt has not been seen, point vt line to index
                vt_to_index[line] = vt_index - skipped_count
                vt_index_mapping[vt_index] = vt_index - skipped_count
                out_obj.write(line)

            vt_index += 1
        else:
            out_obj.write(line)

    # Second pass remaps face vt index
    in_obj.seek(0)
    for line in in_obj.readlines():
        if line[0] != "f":
            continue

        values = line.split()

        for i, coordinates in enumerate(values[1:]):
            v, vt = coordinates.split("/")[:2]
            vt = int(vt)

            if vt in vt_index_mapping.keys():
                vt = vt_index_mapping[vt]

            values[i + 1] = v + "/" + str(vt)

        out_obj.write(" ".join(values) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Reduce the size of a .obj file")
    parser.add_argument("input_file", type = str, help = "Input .obj file name")
    parser.add_argument("--output_file", default = "output.obj", type = str, help = "Output .obj file name")
    args = parser.parse_args()
    process_obj(args.input_file, args.output_file)

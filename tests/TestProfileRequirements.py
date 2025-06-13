# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To read the profiles.
import os #To join paths.
import pytest

##  Makes sure that the variants for the Ultimaker 3 Extended are exactly the
#   same as for the Ultimaker 3.
#
#   Once we have specialised profiles or a mechanism to inherit variants too, we
#   may remove this test and have different profiles for the extended where
#   needed, but until then we should keep them the same. It's happened all too
#   often that we updated the variants for the UM3 but forgot about the UM3E.
@pytest.mark.parametrize("um3_file, um3e_file", [
    #List the corresponding files below.
    ("ultimaker3_aa0.25.inst.cfg", "ultimaker3_extended_aa0.25.inst.cfg"),
    ("ultimaker3_aa0.8.inst.cfg", "ultimaker3_extended_aa0.8.inst.cfg"),
    ("ultimaker3_aa04.inst.cfg", "ultimaker3_extended_aa04.inst.cfg"),
    ("ultimaker3_bb0.8.inst.cfg", "ultimaker3_extended_bb0.8.inst.cfg"),
    ("ultimaker3_bb04.inst.cfg", "ultimaker3_extended_bb04.inst.cfg")
])
def test_ultimaker3extended_variants(um3_file, um3e_file):
    directory = os.path.join(os.path.dirname(__file__), "..", "resources", "variants") #TODO: Hardcoded path relative to this test file.
    um3 = configparser.ConfigParser()
    um3.read_file(open(os.path.join(directory, um3_file), encoding = "utf-8"))
    um3e = configparser.ConfigParser()
    um3e.read_file(open(os.path.join(directory, um3e_file), encoding = "utf-8"))

    assert [value for value in um3["values"]] == [value for value in um3e["values"]]

# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import os


def readFixture(fixture_name: str) -> bytes:
    with open("{}/{}.json".format(os.path.dirname(__file__), fixture_name), "rb") as f:
        return f.read()

def parseFixture(fixture_name: str) -> dict:
    return json.loads(readFixture(fixture_name).decode())

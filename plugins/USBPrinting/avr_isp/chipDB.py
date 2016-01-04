"""
Database of AVR chips for avr_isp programming. Contains signatures and flash sizes from the AVR datasheets.
To support more chips add the relevant data to the avrChipDB list.
This is a python 3 conversion of the code created by David Braam for the Cura project.
"""

avr_chip_db = {
    "ATMega1280": {
            "signature": [0x1E, 0x97, 0x03],
            "pageSize": 128,
            "pageCount": 512,
    },
    "ATMega2560": {
            "signature": [0x1E, 0x98, 0x01],
            "pageSize": 128,
            "pageCount": 1024,
    },
}

def getChipFromDB(sig):
    for chip in avr_chip_db.values():
        if chip["signature"] == sig:
            return chip
    return False


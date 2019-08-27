"""
Module to read intel hex files into binary data blobs.
IntelHex files are commonly used to distribute firmware
See: http://en.wikipedia.org/wiki/Intel_HEX
This is a python 3 conversion of the code created by David Braam for the Cura project.
"""
import io
from typing import List

from UM.Logger import Logger


def readHex(filename: str) -> List[int]:
    """
    Read an verify an intel hex file. Return the data as an list of bytes.
    """
    data = []  # type: List[int]
    extra_addr = 0
    f = io.open(filename, "r", encoding = "utf-8")
    for line in f:
        line = line.strip()
        if len(line) < 1:
            continue
        if line[0] != ":":
            raise Exception("Hex file has a line not starting with ':'")
        rec_len = int(line[1:3], 16)
        addr = int(line[3:7], 16) + extra_addr
        rec_type = int(line[7:9], 16)
        if len(line) != rec_len * 2 + 11:
            raise Exception("Error in hex file: " + line)
        check_sum = 0
        for i in range(0, rec_len + 5):
            check_sum += int(line[i*2+1:i*2+3], 16)
        check_sum &= 0xFF
        if check_sum != 0:
            raise Exception("Checksum error in hex file: " + line)
        
        if rec_type == 0:#Data record
            while len(data) < addr + rec_len:
                data.append(0)
            for i in range(0, rec_len):
                data[addr + i] = int(line[i*2+9:i*2+11], 16)
        elif rec_type == 1:	#End Of File record
            pass
        elif rec_type == 2:	#Extended Segment Address Record
            extra_addr = int(line[9:13], 16) * 16
        else:
            Logger.log("d", "%s, %s, %s, %s, %s", rec_type, rec_len, addr, check_sum, line)
    f.close()
    return data

"""
STK500v2 protocol implementation for programming AVR chips.
The STK500v2 protocol is used by the ArduinoMega2560 and a few other Arduino platforms to load firmware.
This is a python 3 conversion of the code created by David Braam for the Cura project.
"""
import struct
import sys
import time

from serial import Serial   # type: ignore
from serial import SerialException
from serial import SerialTimeoutException
from UM.Logger import Logger

from . import ispBase, intelHex


class Stk500v2(ispBase.IspBase):
    def __init__(self):
        self.serial = None
        self.seq = 1
        self.last_addr = -1
        self.progress_callback = None

    def connect(self, port = "COM22", speed = 115200):
        if self.serial is not None:
            self.close()
        try:
            self.serial = Serial(str(port), speed, timeout=1, writeTimeout=10000)
        except SerialException:
            raise ispBase.IspError("Failed to open serial port")
        except:
            raise ispBase.IspError("Unexpected error while connecting to serial port:" + port + ":" + str(sys.exc_info()[0]))
        self.seq = 1

        #Reset the controller
        for n in range(0, 2):
            self.serial.setDTR(True)
            time.sleep(0.1)
            self.serial.setDTR(False)
            time.sleep(0.1)
        time.sleep(0.2)

        self.serial.flushInput()
        self.serial.flushOutput()
        try:
            if self.sendMessage([0x10, 0xc8, 0x64, 0x19, 0x20, 0x00, 0x53, 0x03, 0xac, 0x53, 0x00, 0x00]) != [0x10, 0x00]:
                raise ispBase.IspError("Failed to enter programming mode")

            self.sendMessage([0x06, 0x80, 0x00, 0x00, 0x00])
            if self.sendMessage([0xEE])[1] == 0x00:
                self._has_checksum = True
            else:
                self._has_checksum = False
        except ispBase.IspError:
            self.close()
            raise
        self.serial.timeout = 5

    def close(self):
        if self.serial is not None:
            self.serial.close()
            self.serial = None

    #Leave ISP does not reset the serial port, only resets the device, and returns the serial port after disconnecting it from the programming interface.
    #	This allows you to use the serial port without opening it again.
    def leaveISP(self):
        if self.serial is not None:
            if self.sendMessage([0x11]) != [0x11, 0x00]:
                raise ispBase.IspError("Failed to leave programming mode")
            ret = self.serial
            self.serial = None
            return ret
        return None

    def isConnected(self):
        return self.serial is not None

    def hasChecksumFunction(self):
        return self._has_checksum

    def sendISP(self, data):
        recv = self.sendMessage([0x1D, 4, 4, 0, data[0], data[1], data[2], data[3]])
        return recv[2:6]

    def writeFlash(self, flash_data):
        #Set load addr to 0, in case we have more then 64k flash we need to enable the address extension
        page_size = self.chip["pageSize"] * 2
        flash_size = page_size * self.chip["pageCount"]
        Logger.log("d", "Writing flash")
        if flash_size > 0xFFFF:
            self.sendMessage([0x06, 0x80, 0x00, 0x00, 0x00])
        else:
            self.sendMessage([0x06, 0x00, 0x00, 0x00, 0x00])
        load_count = (len(flash_data) + page_size - 1) / page_size
        for i in range(0, int(load_count)):
            self.sendMessage([0x13, page_size >> 8, page_size & 0xFF, 0xc1, 0x0a, 0x40, 0x4c, 0x20, 0x00, 0x00] + flash_data[(i * page_size):(i * page_size + page_size)])
            if self.progress_callback is not None:
                if self._has_checksum:
                    self.progress_callback(i + 1, load_count)
                else:
                    self.progress_callback(i + 1, load_count * 2)

    def verifyFlash(self, flash_data):
        if self._has_checksum:
            self.sendMessage([0x06, 0x00, (len(flash_data) >> 17) & 0xFF, (len(flash_data) >> 9) & 0xFF, (len(flash_data) >> 1) & 0xFF])
            res = self.sendMessage([0xEE])
            checksum_recv = res[2] | (res[3] << 8)
            checksum = 0
            for d in flash_data:
                checksum += d
            checksum &= 0xFFFF
            if hex(checksum) != hex(checksum_recv):
                raise ispBase.IspError("Verify checksum mismatch: 0x%x != 0x%x" % (checksum & 0xFFFF, checksum_recv))
        else:
            #Set load addr to 0, in case we have more then 64k flash we need to enable the address extension
            flash_size = self.chip["pageSize"] * 2 * self.chip["pageCount"]
            if flash_size > 0xFFFF:
                self.sendMessage([0x06, 0x80, 0x00, 0x00, 0x00])
            else:
                self.sendMessage([0x06, 0x00, 0x00, 0x00, 0x00])

            load_count = (len(flash_data) + 0xFF) / 0x100
            for i in range(0, int(load_count)):
                recv = self.sendMessage([0x14, 0x01, 0x00, 0x20])[2:0x102]
                if self.progress_callback is not None:
                    self.progress_callback(load_count + i + 1, load_count * 2)
                for j in range(0, 0x100):
                    if i * 0x100 + j < len(flash_data) and flash_data[i * 0x100 + j] != recv[j]:
                        raise ispBase.IspError("Verify error at: 0x%x" % (i * 0x100 + j))

    def sendMessage(self, data):
        message = struct.pack(">BBHB", 0x1B, self.seq, len(data), 0x0E)
        for c in data:
            message += struct.pack(">B", c)
        checksum = 0
        for c in message:
            checksum ^= c
        message += struct.pack(">B", checksum)
        try:
            self.serial.write(message)
            self.serial.flush()
        except SerialTimeoutException:
            raise ispBase.IspError("Serial send timeout")
        self.seq = (self.seq + 1) & 0xFF
        return self.recvMessage()

    def recvMessage(self):
        state = "Start"
        checksum = 0
        while True:
            s = self.serial.read()
            if len(s) < 1:
                raise ispBase.IspError("Timeout")
            b = struct.unpack(">B", s)[0]
            checksum ^= b
            if state == "Start":
                if b == 0x1B:
                    state = "GetSeq"
                    checksum = 0x1B
            elif state == "GetSeq":
                state = "MsgSize1"
            elif state == "MsgSize1":
                msg_size = b << 8
                state = "MsgSize2"
            elif state == "MsgSize2":
                msg_size |= b
                state = "Token"
            elif state == "Token":
                if b != 0x0E:
                    state = "Start"
                else:
                    state = "Data"
                    data = []
            elif state == "Data":
                data.append(b)
                if len(data) == msg_size:
                    state = "Checksum"
            elif state == "Checksum":
                if checksum != 0:
                    state = "Start"
                else:
                    return data

def portList():
    ret = []
    import _winreg  # type: ignore
    key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM") #@UndefinedVariable
    i=0
    while True:
        try:
            values = _winreg.EnumValue(key, i) #@UndefinedVariable
        except:
            return ret
        if "USBSER" in values[0]:
            ret.append(values[1])
        i+=1
    return ret

def runProgrammer(port, filename):
    """ Run an STK500v2 program on serial port 'port' and write 'filename' into flash. """
    programmer = Stk500v2()
    programmer.connect(port = port)
    programmer.programChip(intelHex.readHex(filename))
    programmer.close()

def main():
    """ Entry point to call the stk500v2 programmer from the commandline. """
    import threading
    if sys.argv[1] == "AUTO":
        Logger.log("d", "portList(): ", repr(portList()))
        for port in portList():
            threading.Thread(target=runProgrammer, args=(port,sys.argv[2])).start()
            time.sleep(5)
    else:
        programmer = Stk500v2()
        programmer.connect(port = sys.argv[1])
        programmer.programChip(intelHex.readHex(sys.argv[2]))
        sys.exit(1)

if __name__ == "__main__":
    main()

# Copyright (c) 2016 Thomas Karl Pietrowski

from . import RemovableDrivePlugin

import os, sys
import dbus

from UM.Logger import Logger

DBUS_SYSTEMSESSION  = dbus.SystemBus()
DBUS_PROPERTIES     = 'org.freedesktop.DBus.Properties'
UDISKS2_SERVICE     = '/org/freedesktop/UDisks2'
UDISKS2_NAME        = 'org.freedesktop.UDisks2'
UDISKS2_SERVICE_OBJ = DBUS_SYSTEMSESSION.get_object(UDISKS2_NAME, UDISKS2_SERVICE)
UDISKS2_BLOCK_DEV   = 'org.freedesktop.UDisks2.Block'
UDISKS2_FS_DEV      = 'org.freedesktop.UDisks2.Filesystem'
UDISKS2_DRIVE_DEV   = 'org.freedesktop.UDisks2.Drive'

# For the code below...
PY2 = not sys.version > '3'

#From project firewalld-master, under directory src/firewall, in source file dbus_utils.py.
def dbus_to_python(obj, expected_type=None):
    if obj is None:
        python_obj = obj
    elif isinstance(obj, dbus.Boolean):
        python_obj = bool(obj)
    elif isinstance(obj, dbus.String):
        python_obj = obj.encode('utf-8') if PY2 else str(obj)
    elif PY2 and isinstance(obj, dbus.UTF8String):  # Python3 has no UTF8String
        python_obj = str(obj)
    elif isinstance(obj, dbus.ObjectPath):
        python_obj = str(obj)
    elif isinstance(obj, dbus.Byte) or \
            isinstance(obj, dbus.Int16) or \
            isinstance(obj, dbus.Int32) or \
            isinstance(obj, dbus.Int64) or \
            isinstance(obj, dbus.UInt16) or \
            isinstance(obj, dbus.UInt32) or \
            isinstance(obj, dbus.UInt64):
        python_obj = int(obj)
    elif isinstance(obj, dbus.Double):
        python_obj = float(obj)
    elif isinstance(obj, dbus.Array):
        python_obj = [dbus_to_python(x) for x in obj]
    elif isinstance(obj, dbus.Struct):
        python_obj = tuple([dbus_to_python(x) for x in obj])
    elif isinstance(obj, dbus.Dictionary):
        python_obj = {dbus_to_python(k): dbus_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, bool) or \
         isinstance(obj, str) or isinstance(obj, bytes) or \
         isinstance(obj, int) or isinstance(obj, float) or \
         isinstance(obj, list) or isinstance(obj, tuple) or \
         isinstance(obj, dict):
        python_obj = obj
    else:
        raise TypeError("Unhandled %s" % obj)

    if expected_type is not None:
        if (expected_type == bool and not isinstance(python_obj, bool)) or \
           (expected_type == str and not isinstance(python_obj, str)) or \
           (expected_type == int and not isinstance(python_obj, int)) or \
           (expected_type == float and not isinstance(python_obj, float)) or \
           (expected_type == list and not isinstance(python_obj, list)) or \
           (expected_type == tuple and not isinstance(python_obj, tuple)) or \
           (expected_type == dict and not isinstance(python_obj, dict)):
            raise TypeError("%s is %s, expected %s" % (python_obj, type(python_obj), expected_type))

    return python_obj

def list_to_string(to_be_converted):
    if liste[0]:
        liste = liste[:-1]
    return bytearray(to_be_converted).decode()

class LinuxRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    _drives_readonly = []

    def checkRemovableDrives(self):
        valid_filesystems = ["vfat"] #TODO: Use printer properties and only show valid filesystems
        drives = {}

        devices = []
        udisk2_manager = dbus.Interface(UDISKS2_SERVICE_OBJ, 'org.freedesktop.DBus.ObjectManager')
        udisk2_managed_objects = udisk2_manager.GetManagedObjects()
        if len(udisk2_managed_objects):
            for key, value in udisk2_managed_objects.items():
                key = dbus_to_python(key)
                drive_info = value.get(UDISKS2_BLOCK_DEV, {})
                if drive_info.get("IdUsage") == "filesystem" and drive_info.get("IdType") in valid_filesystems:
                    if drive_info.get('ReadOnly') and : # TODO: Catch this here and warn user about a read-only removable drive
                        if key not in self._drives_readonly:
                            Logger.log("w", "UDisks2: Device %s is read-only!" %())
                            self._drives_readonly.append(key)
                        continue
                    if key not in self._drives.keys():
                        Logger.log("d", "UDisks2: Found new valid device: %s", key)
                    devices.append(key)
        else:
            print("d", "No devices found with UDisks2. This is unlikely! Something is wrong here!")
        
        new_drives_readonly = self._drives_readonly[:]
        for key in self._drives_readonly:
            if key not in udisk2_managed_objects.keys():
                Logger.log("d", "UDisks2: Read-only device has been removed: %s", key)
                new_drives_readonly.remove(key)
        self._drives_readonly = new_drives_readonly
        
        for device in devices:
            object_for_device = DBUS_SYSTEMSESSION.get_object(UDISKS2_NAME, device)
            prop_device = os.path.split(list_to_string(dbus_to_python(object_for_device.Get(UDISKS2_BLOCK_DEV, 'Device', dbus_interface=DBUS_PROPERTIES))))[1]
            prop_label = dbus_to_python(object_for_device.Get(UDISKS2_BLOCK_DEV, 'IdLabel', dbus_interface=DBUS_PROPERTIES))
            #prop_size = object_for_device.Get('org.freedesktop.UDisks2.Block', 'Size', dbus_interface='org.freedesktop.DBus.Properties') # TODO: Filter out devices by size limitation
            prop_mount_points = dbus_to_python(object_for_device.Get(UDISKS2_FS_DEV, 'MountPoints', dbus_interface=DBUS_PROPERTIES))
            if len(prop_mount_points):
                if len(prop_mount_points) > 1:
                    Logger.log("d", "UDisks2: Potential SD card (%s) is mounted multiple times. Ignoring that device...", device)
                    continue
                drives[device] = "%s (%s)" %(prop_label, prop_device)
            else:
                Logger.log("d", "UDisks2: Potential SD card not mounted: %s", str(device))

        return drives

    def performEjectDevice(self, device):
        object_for_device = DBUS_SYSTEMSESSION.get_object(UDISKS2_NAME, device)
        prop_drive = object_for_device.Get(UDISKS2_BLOCK_DEV, 'Drive', dbus_interface=DBUS_PROPERTIES)
        
        Logger.log("d", "UDisks2: Unmounting: %s", device)
        object_for_device.Unmount({'force':True, 'auth.no_user_interaction':True}, dbus_interface=UDISKS2_FS_DEV)
        Logger.log("d", "UDisks2: Unmounted: %s", device)
        object_for_drive = DBUS_SYSTEMSESSION.get_object('org.freedesktop.UDisks2', prop_drive)
        Logger.log("d", "UDisks2: Ejecting : %s", prop_drive)
        object_for_drive.Eject({'force':True, 'auth.no_user_interaction':True}, dbus_interface=UDISKS2_DRIVE_DEV)
        Logger.log("d", "UDisks2: Ejected: %s", prop_drive)

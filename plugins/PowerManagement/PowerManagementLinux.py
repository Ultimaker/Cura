'''
Created on 10.01.2017

@author: thopiekar
'''

import dbus

from UM.Extension import Extension

from UM.Logger import Logger

class PowerManagement(Extension):
    def __init__(self):
        super().__init__()
                
        self.suspendInhibition = None
        
        __init_api_list__ = [self.__init_api_solid__,
                             self.__init_api_freedesktop__,
                             ]
        
        while __init_api_list__:
            try:
                __init_api_list__[0]()
                return
            except:
                del __init_api_list__[0]
        
        Logger.log("e", "We were not able to provide any power management provider!")
        return
    
    def __init_api_solid__(self):
            self.solid_session = None
            devobj = dbus.SessionBus().get_object("org.kde.kded5",
                                                  "/org/kde/Solid/PowerManagement/PolicyAgent")
            self.solid_session = dbus.Interface (devobj,
                                                 "org.kde.Solid.PowerManagement.PolicyAgent")
            
    def __init_api_freedesktop__(self):
            self.freedesktop_session = None
            self.freedesktop_session = dbus.SessionBus().get_object("org.freedesktop.PowerManagement",
                                                                    "/org/freedesktop/PowerManagement/Inhibit")
            
    def setSuspendInhibited(self, state, text=""):
        if state:
            if not (text and type(text) == str):
                if self.solid_session:
                    self.suspendInhibition = self.solid_session.addInhibition(1, "Cura", text)
                elif self.freedesktop_session:
                    self.suspendInhibition = self.freedesktop_session.Inhibit("Cura", text)
            else:
                raise ValueError("e", "Inhibition shall be set, but no text was given!")
                
        else:
            if self.solid_session:
                ret = self.solid_session.ReleaseInhibition(self.suspendInhibition)
                self.suspendInhibition = None
                return ret
            elif self.freedesktop_session:
                ret = self.freedesktop_session.UnInhibit(self.suspendInhibition)
                self.suspendInhibition = None
                return ret

    def hasSuspendInhibition(self):
        if self.freedesktop_session or self.solid_session:
            return self.freedesktop_session.HasInhibit()

    def isSuspendInhibited(self):
        return bool(self.suspendInhibition)
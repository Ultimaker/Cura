'''
Created on 10.01.2017

@author: thopiekar
'''
from UM.Logger import Logger

import ctypes

class PowerManagement(Extension):
    def __init__(self):
        super().__init__()
        
        self.isInhibited = False

    def hasSuspendInhibition(self):
        # Windows should always have.. At least I never heard of 
        return True

    def setSuspendInhibited(self, state, text=""):
        """
        Function used to prevent the computer from going into sleep mode.
        :param prevent: True = Prevent the system from going to sleep from this point on.
        :param prevent: False = No longer prevent the system from going to sleep.
        """
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        # SetThreadExecutionState returns 0 when failed, which is ignored.
        # The function should be supported from Windows XP and up.
        if state and not self.isInhibited:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)  # @UndefinedVariable
            self.isInhibited = True
        elif not state and self.isInhibited:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)  # @UndefinedVariable
            self.isInhibited = False
        else:
            Logger.log("w", "Undefined state! Ignoring the request to make changes on the inhibition of suspend.")
    
    def isSuspendInhibited(self):
        return bool(self.isInhibited)
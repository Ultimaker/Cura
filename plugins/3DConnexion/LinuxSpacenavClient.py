import ctypes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants from spnav.h
SPNAV_EVENT_MOTION = 1
SPNAV_EVENT_BUTTON = 2
SPNAV_EVENT_ANY = SPNAV_EVENT_MOTION | SPNAV_EVENT_BUTTON

# Structures and Union based on spnav.h
class SpnavMotionEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("z", ctypes.c_int),
        ("rx", ctypes.c_int),
        ("ry", ctypes.c_int),
        ("rz", ctypes.c_int),
        ("period", ctypes.c_ushort),
    ]

class SpnavButtonEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("press", ctypes.c_int),
        ("bnum", ctypes.c_int),
    ]

class SpnavEvent(ctypes.Union):
    _fields_ = [
        ("type", ctypes.c_int),
        ("motion", SpnavMotionEvent),
        ("button", SpnavButtonEvent),
    ]

class LinuxSpacenavClient:
    def __init__(self):
        self.lib = None
        self.available = False
        try:
            self.lib = ctypes.CDLL("libspnav.so.0")
            self.available = True
        except OSError:
            try:
                self.lib = ctypes.CDLL("libspnav.so")
                self.available = True
            except OSError:
                logging.warning("libspnav.so.0 or libspnav.so not found. Spacenav functionality will be unavailable.")
                return

        if self.available:
            logging.info("Successfully loaded libspnav.")
            # Define function prototypes
            try:
                self.spnav_open = self.lib.spnav_open
                self.spnav_open.restype = ctypes.c_int
                self.spnav_open.argtypes = []

                self.spnav_close = self.lib.spnav_close
                self.spnav_close.restype = ctypes.c_int
                self.spnav_close.argtypes = []

                self.spnav_fd = self.lib.spnav_fd
                self.spnav_fd.restype = ctypes.c_int
                self.spnav_fd.argtypes = []

                self.spnav_poll_event = self.lib.spnav_poll_event
                self.spnav_poll_event.restype = ctypes.c_int
                self.spnav_poll_event.argtypes = [ctypes.POINTER(SpnavEvent)]

                self.spnav_remove_events = self.lib.spnav_remove_events
                self.spnav_remove_events.restype = ctypes.c_int
                self.spnav_remove_events.argtypes = [ctypes.c_int]
                
                logging.info("Function prototypes defined successfully.")

            except AttributeError as e:
                logging.error(f"Error setting up function prototypes: {e}")
                self.available = False


    def open(self) -> bool:
        if not self.available:
            logging.warning("spnav_open called but library not available.")
            return False
        ret = self.spnav_open()
        if ret == 0:
            logging.info("Successfully opened connection to spacenavd (native protocol).")
            return True
        else:
            # spnav_open returns -1 on error and sets errno.
            # However, ctypes doesn't automatically pick up errno from C.
            # For now, just log a generic error.
            logging.error(f"spnav_open failed with return code {ret}.")
            return False

    def close(self) -> None:
        if not self.available:
            logging.warning("spnav_close called but library not available.")
            return
        ret = self.spnav_close()
        if ret == 0:
            logging.info("Successfully closed connection to spacenavd.")
        else:
            logging.error(f"spnav_close failed with return code {ret}.")


    def poll_event(self) -> SpnavEvent | None:
        if not self.available:
            logging.warning("spnav_poll_event called but library not available.")
            return None
        
        event = SpnavEvent()
        ret = self.spnav_poll_event(ctypes.byref(event))
        if ret > 0:
            # logging.debug(f"spnav_poll_event returned event type: {event.type}") # Too verbose for INFO
            return event
        elif ret == 0:
            # No event pending
            return None
        else:
            # Error
            logging.error(f"spnav_poll_event failed with return code {ret}.")
            return None

    def get_fd(self) -> int:
        if not self.available:
            logging.warning("spnav_fd called but library not available.")
            return -1
        fd = self.spnav_fd()
        if fd == -1:
            logging.error("spnav_fd failed.")
        else:
            logging.info(f"spnav_fd returned file descriptor: {fd}")
        return fd

    def remove_events(self, event_type: int) -> int:
        if not self.available:
            logging.warning("spnav_remove_events called but library not available.")
            return -1 # Or some other error indicator
        
        ret = self.spnav_remove_events(event_type)
        if ret < 0:
            # spnav_remove_events returns number of events removed, or -1 on error
            logging.error(f"spnav_remove_events failed with return code {ret} for event_type {event_type}.")
        else:
            logging.info(f"spnav_remove_events successfully removed {ret} events of type {event_type}.")
        return ret

if __name__ == '__main__':
    logging.info("Attempting to initialize LinuxSpacenavClient for testing...")
    client = LinuxSpacenavClient()

    if client.available:
        logging.info("LinuxSpacenavClient available.")
        if client.open():
            logging.info("Spacenav opened successfully. You can try moving the device.")
            
            # Example of polling for a few events
            for _ in range(5): # Try to read 5 events
                event = client.poll_event()
                if event:
                    if event.type == SPNAV_EVENT_MOTION:
                        logging.info(f"Motion Event: x={event.motion.x}, y={event.motion.y}, z={event.motion.z}, rx={event.motion.rx}, ry={event.motion.ry}, rz={event.motion.rz}")
                    elif event.type == SPNAV_EVENT_BUTTON:
                        logging.info(f"Button Event: press={event.button.press}, bnum={event.button.bnum}")
                else:
                    logging.info("No event polled.")
                    # break # if no event, might not be more immediately

            # Example of getting file descriptor
            fd = client.get_fd()
            logging.info(f"File descriptor: {fd}")

            # Example of removing pending events
            # Note: This might clear events that your application wants. Use carefully.
            # Usually, you'd call this if the event queue is full or if you want to ignore old events.
            # client.remove_events(SPNAV_EVENT_ANY) 
            # logging.info("Attempted to remove any pending events.")

            client.close()
            logging.info("Spacenav closed.")
        else:
            logging.error("Failed to open spacenav.")
    else:
        logging.warning("LinuxSpacenavClient not available. Cannot run tests.")

    logging.info("LinuxSpacenavClient.py basic test finished.")

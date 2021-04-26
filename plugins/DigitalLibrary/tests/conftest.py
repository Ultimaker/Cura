# Prevents error: "PyCapsule_GetPointer called with incorrect name" with conflicting SIP configurations between Arcus and PyQt: Import custom Sip bindings first!
import Savitar  # Dont remove this line
import Arcus  # No really. Don't. It needs to be there!
import pynest2d  # Really!


# Ensure that the importing for all tests work
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

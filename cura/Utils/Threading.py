import functools
import threading

from cura.CuraApplication import CuraApplication


#
# HACK:
#
# In project loading, when override the existing machine is selected, the stacks and containers that are currently
# active in the system will be overridden at runtime. Because the project loading is done in a different thread than
# the Qt thread, something else can kick in the middle of the process. One of them is the rendering. It will access
# the current stacks and container, which have not completely been updated yet, so Cura will crash in this case.
#
# This "@call_on_qt_thread" decorator makes sure that a function will always be called on the Qt thread (blocking).
# It is applied to the read() function of project loading so it can be guaranteed that only after the project loading
# process is completely done, everything else that needs to occupy the QT thread will be executed.
#
class InterCallObject:
    def __init__(self):
        self.finish_event = threading.Event()
        self.result = None


def call_on_qt_thread(func):
    @functools.wraps(func)
    def _call_on_qt_thread_wrapper(*args, **kwargs):
        # If the current thread is the main thread, which is the Qt thread, directly call the function.
        current_thread = threading.current_thread()
        if isinstance(current_thread, threading._MainThread):
            return func(*args, **kwargs)

        def _handle_call(ico, *args, **kwargs):
            ico.result = func(*args, **kwargs)
            ico.finish_event.set()
        inter_call_object = InterCallObject()
        new_args = tuple([inter_call_object] + list(args)[:])
        CuraApplication.getInstance().callLater(_handle_call, *new_args, **kwargs)
        inter_call_object.finish_event.wait()
        return inter_call_object.result
    return _call_on_qt_thread_wrapper

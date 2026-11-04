# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


@unittest.skipUnless(sys.platform == "win32", "Exercises Windows native exception handling")
class TestFaultHandler(unittest.TestCase):
    def testHandledNativeExceptionDoesNotDumpUnrelatedThreads(self):
        # Use a subprocess because a regression can terminate the interpreter.
        # ctypes releases the GIL for RaiseException and translates the handled
        # exception into OSError. The fault handler sees its first-chance event.
        source = textwrap.dedent("""
            import ctypes
            import faulthandler
            import sys
            import threading

            sys.path.insert(0, sys.argv[1])
            from cura.FaultHandler import enableFaultHandler

            ready = threading.Event()
            stop = threading.Event()
            def unrelated_worker():
                ready.set()
                stop.wait()
            worker = threading.Thread(target=unrelated_worker)
            worker.start()
            ready.wait()
            enableFaultHandler()
            try:
                ctypes.windll.kernel32.RaiseException(0x80010012, 0, 0, None)
            except OSError:
                print("handled native exception")
            finally:
                faulthandler.disable()
                stop.set()
                worker.join()
        """)
        result = subprocess.run(
            [sys.executable, "-c", source, str(Path(__file__).resolve().parents[1])],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handled native exception", result.stdout)
        self.assertIn("Windows fatal exception: code 0x80010012", result.stderr)
        self.assertIn("<module>", result.stderr)
        self.assertNotIn("unrelated_worker", result.stderr)


if __name__ == "__main__":
    unittest.main()

# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Type, TYPE_CHECKING, Optional, List

import keyring
from keyring.backend import KeyringBackend
from keyring.errors import NoKeyringError, PasswordSetError, KeyringLocked

from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.OAuth2.Models import BaseModel

# Need to do some extra workarounds on windows:
import sys
from UM.Platform import Platform
if Platform.isWindows():
    if hasattr(sys, "frozen"):
        import win32timezone
    from keyring.backends.Windows import WinVaultKeyring
    keyring.set_keyring(WinVaultKeyring())
if Platform.isOSX():
    from keyring.backends.macOS import Keyring
    keyring.set_keyring(Keyring())
if Platform.isLinux():
    # We do not support the keyring on Linux, so make sure no Keyring backend is loaded, even if there is a system one.
    from keyring.backends.fail import Keyring as NoKeyringBackend
    keyring.set_keyring(NoKeyringBackend())

# Even if errors happen, we don't want this stored locally:
DONT_EVER_STORE_LOCALLY: List[str] = ["refresh_token"]


class KeyringAttribute:
    """
    Descriptor for attributes that need to be stored in the keyring. With Fallback behaviour to the preference cfg file
    """
    def __get__(self, instance: "BaseModel", owner: type) -> Optional[str]:
        if self._store_secure:  # type: ignore
            try:
                value = keyring.get_password("cura", self._keyring_name)
                return value if value != "" else None
            except NoKeyringError:
                self._store_secure = False
                Logger.logException("w", "No keyring backend present")
                return getattr(instance, self._name)
            except KeyringLocked:
                self._store_secure = False
                Logger.log("i", "Access to the keyring was denied.")
                return getattr(instance, self._name)
            except UnicodeDecodeError:
                self._store_secure = False
                Logger.log("w", "The password retrieved from the keyring cannot be used because it contains characters that cannot be decoded.")
                return getattr(instance, self._name)
        else:
            return getattr(instance, self._name)

    def __set__(self, instance: "BaseModel", value: Optional[str]):
        if self._store_secure:
            setattr(instance, self._name, None)
            if value is not None:
                try:
                    keyring.set_password("cura", self._keyring_name, value)
                except (PasswordSetError, KeyringLocked):
                    self._store_secure = False
                    if self._name not in DONT_EVER_STORE_LOCALLY:
                        setattr(instance, self._name, value)
                    Logger.logException("w", "Keyring access denied")
                except NoKeyringError:
                    self._store_secure = False
                    if self._name not in DONT_EVER_STORE_LOCALLY:
                        setattr(instance, self._name, value)
                    Logger.logException("w", "No keyring backend present")
                except BaseException as e:
                    # A BaseException can occur in Windows when the keyring attempts to write a token longer than 1024
                    # characters in the Windows Credentials Manager.
                    self._store_secure = False
                    if self._name not in DONT_EVER_STORE_LOCALLY:
                        setattr(instance, self._name, value)
                    Logger.log("w", "Keyring failed: {}".format(e))
        else:
            setattr(instance, self._name, value)

    def __set_name__(self, owner: type, name: str):
        self._name = "_{}".format(name)
        self._keyring_name = name
        self._store_secure = False
        try:
            self._store_secure = KeyringBackend.viable
        except NoKeyringError:
            Logger.logException("w", "Could not use keyring")
        setattr(owner, self._name, None)

# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Type

import keyring

from UM.Logger import Logger


class KeyringAttribute:
    """
    Descriptor for attributes that need to be stored in the keyring. With Fallback behaviour to the preference cfg file
    """
    def __get__(self, instance: Type["BaseModel"], owner: type) -> str:
        if self._store_secure:
            return keyring.get_password("cura", self._keyring_name)
        else:
            return getattr(instance, self._name)

    def __set__(self, instance: Type["BaseModel"], value: str):
        if self._store_secure:
            setattr(instance, self._name, None)
            try:
                keyring.set_password("cura", self._keyring_name, value)
            except keyring.errors.PasswordSetError:
                self._store_secure = False
                setattr(instance, self._name, value)
                Logger.logException("w", "Keyring access denied")
        else:
            setattr(instance, self._name, value)

    def __set_name__(self, owner: type, name: str):
        self._name = "_{}".format(name)
        self._keyring_name = name
        self._store_secure = False
        try:
            self._store_secure = keyring.backend.KeyringBackend.viable
        except keyring.errors.KeyringError:
            Logger.logException("w", "Could not use keyring")
        setattr(owner, self._name, None)

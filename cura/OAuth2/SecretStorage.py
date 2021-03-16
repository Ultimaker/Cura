# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

import keyring  # TODO: Add to about as dependency

from UM.Logger import Logger


class SecretStorage:
    """
    Secret storage vault. It will by default store a secret in the system keyring. If that fails, is not available or
    not allowed it will store in the Cura preferences. This is the unsafe "old" behaviour
    """

    def __init__(self, preferences: Optional["Preferences"] = None):
        self._stored_secrets = set()
        if preferences:
            self._preferences = preferences
            keys = self._preferences.getValue("general/keyring")
            if keys is not None and keys != '':
                self._stored_secrets = set(keys.split(";"))
            else:
                self._preferences.addPreference("general/keyring", "{}")

    def __delitem__(self, key: str):
        if key in self._stored_secrets:
            self._stored_secrets.remove(key)
            self._preferences.setValue("general/keyring", ";".join(self._stored_secrets))
            keyring.delete_password("cura", key)
        else:
            # TODO: handle removal of secret from preferences
            pass

    def __setitem__(self, key: str, value: str):
        try:
            keyring.set_password("cura", key, value)
            self._stored_secrets.add(key)
            self._preferences.setValue("general/{key}".format(key = key), None)
        except:
            Logger.logException("w", "Could not store {key} in keyring.".format(key = key))
            if key in self._stored_secrets:
                self._stored_secrets.remove(key)
            self._preferences.addPreference("general/{key}".format(key = key), "{}")
            self._preferences.setValue("general/{key}".format(key = key), value)
        self._preferences.setValue("general/keyring", ";".join(self._stored_secrets))

    def __getitem__(self, key: str) -> Optional[str]:
        secret = None
        if key in self._stored_secrets:
            try:
                secret = keyring.get_password("cura", key)
            except:
                secret = self._preferences.getValue("general/{key}".format(key = key))
                Logger.logException("w", "{key} obtained from preferences, consider giving Cura access to the keyring".format(key = key))
        else:
            secret = self._preferences.getValue(f"general/{key}")
            Logger.logException("w", "{key} obtained from preferences, consider giving Cura access to the keyring".format(key = key))
        if secret is None or secret == '':
            Logger.logException("w", "Could not load {key}".format(key = key))
        return secret

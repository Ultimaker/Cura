from typing import Optional

import keyring  # TODO: Add to about as dependency

from UM.Logger import Logger


class SecretStorage:
    def __init__(self, preferences: Optional["Preferences"] = None):
        self._stored_secrets = set()
        if preferences:
            self._preferences = preferences
            keys = self._preferences.getValue("general/keyring")
            if keys is not None and keys != '':
                self._stored_secrets = set(keys.split(";"))
            else:
                self._preferences.addPreference("general/keyring", "{}")

    def __delitem__(self, key):
        if key in self._stored_secrets:
            self._stored_secrets.remove(key)
            self._preferences.setValue("general/keyring", ";".join(self._stored_secrets))
            keyring.delete_password("cura", key)
        else:
            # TODO: handle removal of secret from preferences
            pass

    def __setitem__(self, key, value):
        try:
            keyring.set_password("cura", key, value)
            self._stored_secrets.add(key)
            self._preferences.setValue(f"general/{key}", None)
        except:
            Logger.logException("w", f"Could not store {key} in keyring.")
            if key in self._stored_secrets:
                self._stored_secrets.remove(key)
            self._preferences.addPreference("general/{key}".format(key=key), "{}")
            self._preferences.setValue("general/{key}".format(key=key), value)
        self._preferences.setValue("general/keyring", ";".join(self._stored_secrets))

    def __getitem__(self, key):
        secret = self._preferences.getValue(f"general/{key}")
        if key in self._stored_secrets:
            try:
                secret = keyring.get_password("cura", key)
            except:
                if secret:
                    Logger.logException("w",
                                        f"{key} obtained from preferences, consider giving Cura access to the keyring")
        if secret is None or secret == 'null':
            Logger.logException("w", f"Could not load {key}")
        return secret

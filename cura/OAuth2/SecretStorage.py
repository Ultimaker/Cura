import keyring


class SecretStorage:
    def __init__(self):
        self._stored_secrets = []

    def __delitem__(self, key):
        if key in self._stored_secrets:
            del self._stored_secrets[key]
            keyring.delete_password("cura", key)

    def __setitem__(self, key, value):
        self._stored_secrets.append(key)
        keyring.set_password("cura", key, value)

    def __getitem__(self, key):
        if key in self._stored_secrets:
            return keyring.get_password("cura", key)
        return None

from UM.Application import Application

import json
import time

class SessionManager:
    bcn3d_auth_data_key = "general/bcn3d_auth_data"

    def __init__(self):
        super().__init__()
        if SessionManager.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        self._access_token = None
        self._refresh_token = None

        self._preferences = Application.getInstance().getPreferences()

    def initialize(self):
        self._preferences.addPreference(self.bcn3d_auth_data_key, "{}")
        auth_data = json.loads(self._preferences.getValue(self.bcn3d_auth_data_key))
        self._access_token = auth_data.get("access_token")
        self._refresh_token = auth_data.get("refresh_token")
        self._last_request = auth_data.get("last_request")
        self._expires = auth_data.get("expires")
        if self._access_token and not self._expires:
            self.clearSession()

    def getAccessToken(self):
        return self._access_token

    def getRefreshToken(self):
        return self._refresh_token

    def setOuathToken(self, data):
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._last_request = int(time.time())
        self._expires = self._last_request + data['expires_in']
        self.storeSession()

    def setAccessToken(self, access_token):
        self._access_token = access_token

    def setRefreshToken(self, refresh_token):
        self._refresh_token = refresh_token

    def tokenIsExpired(self):
        if self._expires == None:
            return True
        return (self._expires - int(time.time()) < 60)

    def storeSession(self):
        self._preferences.setValue(self.bcn3d_auth_data_key, json.dumps(
            {
                "access_token": self._access_token, 
                "refresh_token": self._refresh_token, 
                "last_request" : self._last_request,
                "expires" : self._expires
            }
        ))

    def clearSession(self):
        self._access_token = None
        self._refresh_token = None
        self._last_request = None
        self._expires = None
        self.storeSession()

    @classmethod
    def getInstance(cls) -> "SessionManager":
        if not cls.__instance:
            cls.__instance = SessionManager()
        return cls.__instance

    __instance = None

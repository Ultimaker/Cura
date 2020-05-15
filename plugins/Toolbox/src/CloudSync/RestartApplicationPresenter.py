from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication


class RestartApplicationPresenter:
    """Presents a dialog telling the user that a restart is required to apply changes
    
    Since we cannot restart Cura, the app is closed instead when the button is clicked
    """
    def __init__(self, app: CuraApplication) -> None:
        self._app = app
        self._i18n_catalog = i18nCatalog("cura")

    def present(self) -> None:
        app_name = self._app.getApplicationDisplayName()

        message = Message(self._i18n_catalog.i18nc(
            "@info:generic",
            "You need to quit and restart {} before changes have effect.", app_name
        ))

        message.addAction("quit",
                          name="Quit " + app_name,
                          icon = "",
                          description="Close the application",
                          button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)

        message.actionTriggered.connect(self._quitClicked)
        message.show()

    def _quitClicked(self, *_):
        self._app.windowClosed()

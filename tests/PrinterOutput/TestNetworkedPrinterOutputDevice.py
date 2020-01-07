import time
from unittest.mock import MagicMock, patch

from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtCore import QUrl
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionState


def test_properties():
    properties = { b"firmware_version": b"12", b"printer_type": b"BHDHAHHADAD", b"address": b"ZOMG", b"name": b":(", b"testProp": b"zomg"}
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id = "test", address = "127.0.0.1", properties = properties)
    assert output_device.address == "ZOMG"
    assert output_device.firmwareVersion == "12"
    assert output_device.printerType == "BHDHAHHADAD"
    assert output_device.ipAddress == "127.0.0.1"
    assert output_device.name == ":("
    assert output_device.key == "test"
    assert output_device.getProperties() == properties

    assert output_device.getProperty("testProp") == "zomg"
    assert output_device.getProperty("whateverr") == ""


def test_authenticationState():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})

    output_device.setAuthenticationState(AuthState.Authenticated)

    assert output_device.authenticationState == AuthState.Authenticated


def test_post():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})
    mocked_network_manager = MagicMock()
    output_device._manager = mocked_network_manager

    # Create a fake reply (we cant use a QReply, since those are abstract C++)
    reply = MagicMock()
    reply.operation = MagicMock(return_value=QNetworkAccessManager.PostOperation)
    reply.url = MagicMock(return_value=QUrl("127.0.0.1"))
    mocked_network_manager.post = MagicMock(return_value = reply)

    mocked_callback_handler = MagicMock()
    output_device.post("whatever", "omgzomg", on_finished = mocked_callback_handler.onFinished)

    # So we now fake that the request was sucesful.
    output_device._handleOnFinished(reply)

    # We expect to get a callback regarding this.
    mocked_callback_handler.onFinished.assert_called_once_with(reply)


def test_get():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})
    mocked_network_manager = MagicMock()
    output_device._manager = mocked_network_manager

    # Create a fake reply (we cant use a QReply, since those are abstract C++)
    reply = MagicMock()
    reply.operation = MagicMock(return_value=QNetworkAccessManager.PostOperation)
    reply.url = MagicMock(return_value=QUrl("127.0.0.1"))
    mocked_network_manager.get = MagicMock(return_value=reply)

    mocked_callback_handler = MagicMock()
    output_device.get("whatever", on_finished=mocked_callback_handler.onFinished)

    # So we now fake that the request was sucesful.
    output_device._handleOnFinished(reply)

    # We expect to get a callback regarding this.
    mocked_callback_handler.onFinished.assert_called_once_with(reply)


def test_delete():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})
    mocked_network_manager = MagicMock()
    output_device._manager = mocked_network_manager

    # Create a fake reply (we cant use a QReply, since those are abstract C++)
    reply = MagicMock()
    reply.operation = MagicMock(return_value=QNetworkAccessManager.PostOperation)
    reply.url = MagicMock(return_value=QUrl("127.0.0.1"))
    mocked_network_manager.deleteResource = MagicMock(return_value=reply)

    mocked_callback_handler = MagicMock()
    output_device.delete("whatever", on_finished=mocked_callback_handler.onFinished)

    # So we now fake that the request was sucesful.
    output_device._handleOnFinished(reply)

    # We expect to get a callback regarding this.
    mocked_callback_handler.onFinished.assert_called_once_with(reply)


def test_put():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})
    mocked_network_manager = MagicMock()
    output_device._manager = mocked_network_manager

    # Create a fake reply (we cant use a QReply, since those are abstract C++)
    reply = MagicMock()
    reply.operation = MagicMock(return_value=QNetworkAccessManager.PostOperation)
    reply.url = MagicMock(return_value=QUrl("127.0.0.1"))
    mocked_network_manager.put = MagicMock(return_value = reply)

    mocked_callback_handler = MagicMock()
    output_device.put("whatever", "omgzomg", on_finished = mocked_callback_handler.onFinished)

    # So we now fake that the request was sucesful.
    output_device._handleOnFinished(reply)

    # We expect to get a callback regarding this.
    mocked_callback_handler.onFinished.assert_called_once_with(reply)


def test_timeout():
    with patch("UM.Qt.QtApplication.QtApplication.getInstance"):
        output_device = NetworkedPrinterOutputDevice(device_id="test", address="127.0.0.1", properties={})
    output_device.setConnectionState(ConnectionState.Connected)

    assert output_device.connectionState == ConnectionState.Connected
    output_device._update()
    # Pretend we didn't get any response for 15 seconds
    output_device._last_response_time = time.time() - 15
    # But we did recently ask for a response!
    output_device._last_request_time = time.time() - 5
    output_device._update()

    # The connection should now be closed, since it went into timeout.
    assert output_device.connectionState == ConnectionState.Closed



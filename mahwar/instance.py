"""One per-user instance; subsequent launches activate the existing main window."""
from __future__ import annotations
import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def instance_name(user_home=None):
    # Stable across Windows launches and EXE locations; separate user profiles.
    home = str(user_home or Path.home()).casefold()
    suffix = hashlib.sha256(home.encode("utf-8")).hexdigest()[:20]
    return "MahwarFocusSingleInstance_" + suffix


class SingleInstanceCoordinator(QObject):
    activated = Signal()

    def __init__(self, name=None, parent=None):
        super().__init__(parent)
        self.name = name or instance_name()
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._on_connection)

    def _signal_existing(self):
        client = QLocalSocket(self)
        client.connectToServer(self.name)
        connected = client.waitForConnected(450)
        if connected:
            client.write(b"SHOW\n")
            client.flush()
            client.waitForBytesWritten(450)
            client.disconnectFromServer()
        client.deleteLater()
        return connected

    def claim_or_activate(self):
        """True=primary instance; False=notified already-running instance."""
        if self._signal_existing():
            return False
        if self.server.listen(self.name):
            return True
        # Another instance could have claimed the server during the first probe.
        if self._signal_existing():
            return False
        raise RuntimeError("تعذّر حجز قناة التطبيق؛ تأكد من عدم وجود نسخة أخرى قيد التشغيل.")

    def _on_connection(self):
        while self.server.hasPendingConnections():
            client = self.server.nextPendingConnection()
            self.activated.emit()
            client.disconnectFromServer()
            client.deleteLater()

    def close(self):
        self.server.close()

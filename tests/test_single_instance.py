"""Single-instance signaling via Qt local IPC, without starting two tray icons."""
import uuid

from PySide6.QtWidgets import QApplication
from mahwar.instance import SingleInstanceCoordinator, instance_name


def test_unique_per_profile_name():
    assert instance_name("C:/Users/A") == instance_name("c:/users/a")
    assert instance_name("C:/Users/A") != instance_name("C:/Users/B")


def test_second_launch_signals_first():
    app = QApplication.instance() or QApplication([])
    name = "MahwarFocus_Test_" + uuid.uuid4().hex
    first = SingleInstanceCoordinator(name)
    second = SingleInstanceCoordinator(name)
    received = []
    first.activated.connect(lambda: received.append(True))
    try:
        assert first.claim_or_activate() is True
        assert second.claim_or_activate() is False
        # Dispatch Qt server's newConnection signal.
        for _ in range(30):
            app.processEvents()
            if received:
                break
        assert received, "Second launch must activate the existing process"
    finally:
        first.close()
        second.close()

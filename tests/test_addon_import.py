import importlib.util
import sys
import types
from pathlib import Path


def test_addon_init_can_load_helper_module_from_sibling_file():
    root = Path(__file__).resolve().parent.parent
    addon_init_path = root / "__init__.py"

    fake_aqt = types.ModuleType("aqt")
    fake_aqt.mw = types.SimpleNamespace(form=types.SimpleNamespace(menuTools=types.SimpleNamespace(addAction=lambda action: None)))

    fake_qt = types.ModuleType("aqt.qt")

    class DummyWidget:
        def __init__(self, *args, **kwargs):
            pass

    class DummySignal:
        def connect(self, *args, **kwargs):
            return None

    class DummyQt:
        Window = 0
        WindowStaysOnTopHint = 0
        AlignCenter = 0

    fake_qt.QAction = lambda *args, **kwargs: types.SimpleNamespace(triggered=DummySignal())
    fake_qt.QApplication = types.SimpleNamespace(desktop=lambda: types.SimpleNamespace(availableGeometry=lambda dialog: None))
    fake_qt.QComboBox = DummyWidget
    fake_qt.QDialog = DummyWidget
    fake_qt.QHBoxLayout = DummyWidget
    fake_qt.QLabel = DummyWidget
    fake_qt.QPlainTextEdit = DummyWidget
    fake_qt.QProgressBar = DummyWidget
    fake_qt.QPushButton = DummyWidget
    fake_qt.QThread = DummyWidget
    fake_qt.QTimer = DummyWidget
    fake_qt.QVBoxLayout = DummyWidget
    fake_qt.QObject = object
    fake_qt.pyqtSignal = lambda *args, **kwargs: DummySignal()
    fake_qt.Qt = DummyQt

    fake_utils = types.ModuleType("aqt.utils")
    fake_utils.showInfo = lambda *args, **kwargs: None

    sys.modules["aqt"] = fake_aqt
    sys.modules["aqt.qt"] = fake_qt
    sys.modules["aqt.utils"] = fake_utils

    try:
        spec = importlib.util.spec_from_file_location("test_addon_init", addon_init_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        assert hasattr(module, "generator")
    finally:
        sys.modules.pop("test_addon_init", None)

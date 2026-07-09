import importlib.util
import os
import pathlib
import threading
import types

try:
    from aqt import mw
    from aqt.qt import (
        QAction,
        QApplication,
        QComboBox,
        QDialog,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QThread,
        QTimer,
        QVBoxLayout,
        QObject,
        pyqtSignal,
        Qt,
    )
    from aqt.utils import showInfo
except ImportError:
    class _DummySignal:
        def connect(self, *args, **kwargs):
            return None

        def emit(self, *args, **kwargs):
            return None

    class _DummyWidget:
        exec = staticmethod(lambda *args, **kwargs: None)

        def __init__(self, *args, **kwargs):
            self.started = _DummySignal()
            self.finished = _DummySignal()
            self.timeout = _DummySignal()
            self.exec = lambda *args, **kwargs: None
            self.triggered = _DummySignal()

        def connect(self, *args, **kwargs):
            return None

        def show(self, *args, **kwargs):
            return None

        def hide(self, *args, **kwargs):
            return None

        def setAttribute(self, *args, **kwargs):
            return None

        def setWindowTitle(self, *args, **kwargs):
            return None

        def setWindowFlags(self, *args, **kwargs):
            return None

        def setWindowModality(self, *args, **kwargs):
            return None

        def setGeometry(self, *args, **kwargs):
            return None

        def setMinimumWidth(self, *args, **kwargs):
            return None

        def addWidget(self, *args, **kwargs):
            return None

        def addSpacing(self, *args, **kwargs):
            return None

        def addLayout(self, *args, **kwargs):
            return None

        def addStretch(self, *args, **kwargs):
            return None

        def setRange(self, *args, **kwargs):
            return None

        def setValue(self, *args, **kwargs):
            return None

        def setPlaceholderText(self, *args, **kwargs):
            return None

        def setFixedHeight(self, *args, **kwargs):
            return None

        def setWordWrap(self, *args, **kwargs):
            return None

        def setText(self, *args, **kwargs):
            return None

        def toPlainText(self, *args, **kwargs):
            return ""

        def currentText(self, *args, **kwargs):
            return ""

        def addItems(self, *args, **kwargs):
            return None

        def exec(self, *args, **kwargs):
            return None

        def start(self, *args, **kwargs):
            return None

        def quit(self, *args, **kwargs):
            return None

        def deleteLater(self, *args, **kwargs):
            return None

        def setSingleShot(self, *args, **kwargs):
            return None

    class _DummyQt:
        Window = 0
        WindowStaysOnTopHint = 0
        AlignCenter = 0
        NonModal = 0
        WA_DeleteOnClose = 0

    class _DummyApplication:
        @staticmethod
        def instance():
            return None

        @staticmethod
        def screens():
            return []

        @staticmethod
        def desktop():
            return None

    mw = types.SimpleNamespace(form=types.SimpleNamespace(menuTools=types.SimpleNamespace(addAction=lambda action: None)))
    QAction = lambda *args, **kwargs: _DummyWidget()
    QApplication = _DummyApplication
    QComboBox = _DummyWidget
    QDialog = _DummyWidget
    QHBoxLayout = _DummyWidget
    QLabel = _DummyWidget
    QPlainTextEdit = _DummyWidget
    QProgressBar = _DummyWidget
    QPushButton = _DummyWidget
    QThread = _DummyWidget
    QTimer = _DummyWidget
    QVBoxLayout = _DummyWidget
    QObject = object
    pyqtSignal = lambda *args, **kwargs: _DummySignal()
    Qt = _DummyQt
    showInfo = lambda *args, **kwargs: None

try:
    from .magic_image_fetcher import debug, load_config, process_notes
except ImportError:
    module_path = pathlib.Path(__file__).resolve().with_name("magic_image_fetcher.py")
    spec = importlib.util.spec_from_file_location("magic_image_fetcher", module_path)
    if spec is None or spec.loader is None:
        raise
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    debug = module.debug
    load_config = module.load_config
    process_notes = module.process_notes

# Qt6 compatibility: some PyQt6 builds expose enums under WindowType/AlignmentFlag
try:
    _QT_WINDOW = Qt.Window
    _QT_STAY_ON_TOP = Qt.WindowStaysOnTopHint
    _QT_ALIGN_CENTER = Qt.AlignCenter
except AttributeError:
    try:
        _QT_WINDOW = Qt.WindowType.Window
        _QT_STAY_ON_TOP = Qt.WindowType.WindowStaysOnTopHint
        _QT_ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    except Exception:
        _QT_WINDOW = 0
        _QT_STAY_ON_TOP = 0
        _QT_ALIGN_CENTER = 0

try:
    _QT_NON_MODAL = Qt.NonModal
except AttributeError:
    try:
        _QT_NON_MODAL = Qt.WindowModality.NonModal
    except Exception:
        _QT_NON_MODAL = 0

try:
    _WA_DELETE_ON_CLOSE = Qt.WA_DeleteOnClose
except AttributeError:
    try:
        _WA_DELETE_ON_CLOSE = Qt.WidgetAttribute.WA_DeleteOnClose
    except Exception:
        _WA_DELETE_ON_CLOSE = 0

addon_dir = os.path.abspath(os.path.dirname(__file__))
log_path = os.path.join(addon_dir, "debug.log")


def _get_available_screen_geometry():
    try:
        app = QApplication.instance()
        if app is not None:
            if hasattr(app, "primaryScreen"):
                screen = app.primaryScreen()
                if screen is not None and hasattr(screen, "availableGeometry"):
                    return screen.availableGeometry()
            if hasattr(QApplication, "screens"):
                screens = QApplication.screens()
                if screens:
                    screen = screens[0]
                    if hasattr(screen, "availableGeometry"):
                        return screen.availableGeometry()
            if hasattr(QApplication, "desktop"):
                desktop = QApplication.desktop()
                if desktop is not None and hasattr(desktop, "availableGeometry"):
                    geom = desktop.availableGeometry()
                    if geom is not None:
                        return geom
    except Exception:
        pass
    return None


class GenerationSettingsDialog(QDialog):
    start_requested = pyqtSignal(str, str)
    exec_ = QDialog.exec

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🤖 AI 圖片生成助手")
        self.setWindowFlags(_QT_WINDOW | _QT_STAY_ON_TOP)
        self.setWindowModality(_QT_NON_MODAL)
        self.setAttribute(_WA_DELETE_ON_CLOSE, True)
        self.setMinimumWidth(360)

        self.deck_combo = QComboBox(self)
        self.deck_combo.setEditable(False)
        self.extra_prompt_input = QPlainTextEdit(self)
        self.extra_prompt_input.setPlaceholderText("可留空")
        self.extra_prompt_input.setFixedHeight(90)
        self.start_button = QPushButton("開始生成", self)

        deck_label = QLabel("Deck：")
        prompt_label = QLabel("額外提示詞：")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🤖 AI 圖片生成助手"))
        layout.addWidget(deck_label)
        layout.addWidget(self.deck_combo)
        layout.addWidget(prompt_label)
        layout.addWidget(self.extra_prompt_input)
        layout.addSpacing(10)
        layout.addWidget(self.start_button, 0, _QT_ALIGN_CENTER)

        self.start_button.clicked.connect(self._on_start)

        self._populate_decks()

    def _populate_decks(self):
        deck_names = mw.col.decks.all_names_and_ids()
        self.deck_combo.addItems([deck.name for deck in deck_names])

    def _on_start(self):
        deck_name = self.deck_combo.currentText().strip()
        if not deck_name:
            showInfo("請選擇一個 Deck。")
            return
        self.start_requested.emit(deck_name, self.extra_prompt_input.toPlainText())
        self.accept()


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🤖 AI 圖片生成助手")
        self.setWindowFlags(_QT_WINDOW)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        self.current_count_label = QLabel("目前處理：0 / 0")
        self.current_word_label = QLabel("目前單字：")
        self.generated_label = QLabel("已生成：0")
        self.skipped_label = QLabel("已跳過：0")
        self.failed_label = QLabel("失敗：0")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.cancel_button = QPushButton("取消生成")
        self.confirm_button = QPushButton("確認")
        self.confirm_button.hide()
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🤖 AI 圖片生成助手"))
        layout.addWidget(self.current_count_label)
        layout.addWidget(self.current_word_label)
        layout.addWidget(self.generated_label)
        layout.addWidget(self.skipped_label)
        layout.addWidget(self.failed_label)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(10)
        layout.addWidget(self.summary_label)
        layout.addSpacing(10)
        button_row = QHBoxLayout()
        button_row.addWidget(self.cancel_button)
        button_row.addStretch()
        button_row.addWidget(self.confirm_button)
        layout.addLayout(button_row)

        self.cancel_button.clicked.connect(self._cancel_clicked)
        self.confirm_button.clicked.connect(self.close)
        self._cancel_handler = None
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self.close)
        self._completed = False

    def set_cancel_handler(self, handler):
        self._cancel_handler = handler

    def _cancel_clicked(self):
        if self._cancel_handler:
            self._cancel_handler()

    def update_progress(self, processed, total, current_word, success, skipped, failed):
        self.current_count_label.setText(f"目前處理：{processed} / {total}")
        self.current_word_label.setText(f"目前單字：{current_word or '-'}")
        self.generated_label.setText(f"已生成：{success}")
        self.skipped_label.setText(f"已跳過：{skipped}")
        self.failed_label.setText(f"失敗：{failed}")
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(processed)

    def show_completed(self, stats, cancelled=False):
        self._completed = True
        self.cancel_button.hide()
        self.confirm_button.show()
        self.progress_bar.setValue(stats.get("processed", 0))
        if cancelled:
            self.summary_label.setText(
                f"⚠️ 已取消生成\n\n總卡片：{stats.get('total', 0)}\n已完成：{stats.get('processed', 0)}\n跳過：{stats.get('skipped', 0)}\n失敗：{stats.get('failed', 0)}\n尚未處理：{max(stats.get('total', 0) - stats.get('processed', 0), 0)}\n耗時：{self._format_elapsed(stats.get('elapsed_seconds', 0))}"
            )
        else:
            self.summary_label.setText(
                f"✅ 圖片生成完成\n\n總卡片：{stats.get('total', 0)}\n成功：{stats.get('success', 0)}\n跳過：{stats.get('skipped', 0)}\n失敗：{stats.get('failed', 0)}\n耗時：{self._format_elapsed(stats.get('elapsed_seconds', 0))}"
            )
        self._auto_close_timer.start(10000)

    def _format_elapsed(self, elapsed_seconds):
        minutes, seconds = divmod(int(elapsed_seconds), 60)
        return f"{minutes} 分 {seconds} 秒"


class GenerationWorker(QObject):
    progress = pyqtSignal(int, int, str, int, int, int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, deck_name, extra_prompt):
        super().__init__()
        self.deck_name = deck_name
        self.extra_prompt = extra_prompt
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            stats = process_notes(
                self.deck_name,
                extra_prompt=self.extra_prompt,
                progress_callback=self._emit_progress,
                cancel_event=self.cancel_event,
            )
            self.finished.emit(stats)
        except Exception as exc:
            debug(f"❌ Generation thread error: {exc}")
            self.error.emit(str(exc))

    def _emit_progress(self, processed, total, current_word, success, skipped, failed):
        self.progress.emit(processed, total, current_word, success, skipped, failed)


class MagicImageGenerator:
    def __init__(self):
        self._generation_running = False
        self._progress_dialog = None
        self._worker = None
        self._thread = None

    def run(self):
        debug("🚀 run_image_script() called")
        config = load_config()
        if not config.get("GEMINI_API_KEY"):
            debug("⚠️ Missing Gemini API key in config.json.")
            showInfo("config.json 中缺少 GEMINI_API_KEY。")
            return

        if self._generation_running:
            showInfo("目前已有生成工作正在執行。請等待完成或取消目前工作。")
            return

        deck_name = self._resolve_default_deck_name()
        if not deck_name:
            showInfo("找不到可用的 Deck，請先建立一個牌組。")
            return

        self._start_generation(deck_name, "")

    def _resolve_default_deck_name(self):
        try:
            deck_names = mw.col.decks.all_names_and_ids()
            if deck_names:
                return deck_names[0].name
        except Exception:
            pass

        return ""

    def _start_generation(self, deck_name, extra_prompt):
        self._generation_running = True
        self._progress_dialog = ProgressDialog(mw)
        self._progress_dialog.set_cancel_handler(self._cancel_generation)
        self._progress_dialog.show()
        self._move_to_center(self._progress_dialog)
        self._progress_dialog.raise_()
        self._progress_dialog.activateWindow()

        self._worker = GenerationWorker(deck_name, extra_prompt)
        self._thread = QThread(mw)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._progress_dialog.update_progress)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.error.connect(self._on_generation_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _cancel_generation(self):
        if self._worker and not self._generation_running:
            return
        debug("⚠️ Cancel requested by user")
        if self._worker:
            self._worker.cancel()

    def _on_generation_finished(self, stats):
        self._generation_running = False
        if self._progress_dialog:
            self._progress_dialog.show_completed(stats, cancelled=stats.get("cancelled", False))
            self._move_to_top_right(self._progress_dialog)

    def _on_generation_error(self, message):
        self._generation_running = False
        if self._progress_dialog:
            self._progress_dialog.show_completed({"total": 0, "processed": 0, "success": 0, "skipped": 0, "failed": 0, "elapsed_seconds": 0}, cancelled=False)
            self._move_to_top_right(self._progress_dialog)
        showInfo(message)

    def _move_to_center(self, dialog):
        """Position dialog in the center of the screen, without blocking Anki."""
        try:
            screen = _get_available_screen_geometry()
            if screen is not None:
                x = screen.x() + (screen.width() - dialog.width()) // 2
                y = screen.y() + (screen.height() - dialog.height()) // 2
                dialog.move(x, y)
        except Exception:
            pass


generator = MagicImageGenerator()

action = QAction("🤖 AI 圖片生成助手", mw)
action.triggered.connect(generator.run)
mw.form.menuTools.addAction(action)

debug("✅ Menu action attached successfully")

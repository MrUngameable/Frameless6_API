from PySide6.QtCore import Qt, Signal, QEventLoop, QPoint, QSize
from PySide6.QtGui import QCloseEvent, QKeyEvent, QPixmap, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QApplication
)

from enum import IntEnum
import sys
import ctypes


RESIZE_MARGIN = 8


class FramelessWindow(QMainWindow):
    """
    Reusable frameless window container.
    Acts as a drop-in replacement for QMainWindow.
    """

    closeRequested = Signal()

    def __init__(
            self,
            app_name: str | None = None,
            app_icon: QIcon | None = None
    ):
        super().__init__()

        # App Identity
        self._app_name = app_name or "Application"

        QApplication.instance().setApplicationName(self._app_name)
        QApplication.instance().setApplicationDisplayName(self._app_name)
        self.setWindowTitle(self._app_name)

        if app_icon:
            self.setWindowIcon(app_icon)
            QApplication.instance().setWindowIcon(app_icon)

        # Group windows
        self._apply_windows_app_id()

        self.setObjectName("FramelessWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMouseTracking(True)

        self._resize_edges = Qt.Edges()
        self._title_bar: QWidget | None = None

        # Root widget (draws border)
        self._root = QWidget(self)
        self._root.setObjectName("Root")
        self.setCentralWidget(self._root)

        self.setStyleSheet("""
        #Root {
            background-color: #1e1e1e;
            border: 1px solid #525252;
        }
        """)

        # Layout inside root
        self._layout = QVBoxLayout(self._root)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Native-style close pipeline
        self.closeRequested.connect(self.close)

    # ---------------- PUBLIC API ---------------- #

    def setTitleBar(self, title_bar: QWidget):
        self._title_bar = title_bar

    def addWidget(self, widget: QWidget):
        self._layout.addWidget(widget)

    # ---------------- WINDOW LIFECYCLE ---------------- #

    def closeEvent(self, event: QCloseEvent):
        """
        Native-equivalent close event.
        Override in subclasses to intercept / cancel close.
        """
        #print("closeEvent fired")
        event.accept()  # or event.ignore()

    # ---------------- RESIZE HANDLING ---------------- #

    def mouseMoveEvent(self, event):
        if self.isMaximized():
            self.unsetCursor()
            return

        pos = event.position().toPoint()
        rect = self.rect()
        edges = Qt.Edges()

        if pos.x() <= RESIZE_MARGIN:
            edges |= Qt.LeftEdge
        if pos.x() >= rect.width() - RESIZE_MARGIN:
            edges |= Qt.RightEdge
        if pos.y() <= RESIZE_MARGIN:
            edges |= Qt.TopEdge
        if pos.y() >= rect.height() - RESIZE_MARGIN:
            edges |= Qt.BottomEdge

        self._resize_edges = edges

        if edges in (Qt.LeftEdge, Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edges in (Qt.TopEdge, Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        elif edges in (Qt.TopEdge | Qt.LeftEdge, Qt.BottomEdge | Qt.RightEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges in (Qt.TopEdge | Qt.RightEdge, Qt.BottomEdge | Qt.LeftEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and self._resize_edges
            and not self.isMaximized()
        ):
            self.windowHandle().startSystemResize(self._resize_edges)
            event.accept()
            return

        super().mousePressEvent(event)

    # ------------------- App Identity ------------------- #

    def setAppName(self, name: str):
        self._app_name = name
        self.setWindowTitle(name)

        QApplication.instance().setApplicationName(name)
        QApplication.instance().setApplicationDisplayName(name)

        self.setWindowTitle(name)

        # Keep custom titlebar in sync if present
        if self._title_bar and hasattr(self._title_bar, "setTitle"):
            self._title_bar.setTitle(name)

    # ---------------- Window Grouping ID ---------------- #

    def _apply_windows_app_id(self):
        if sys.platform != "win32":
            return
        
        # stable, readable, deterministic
        safe_name = self._app_name.lower().replace(" ", "")
        app_id = f"com.projectironman.{safe_name}"    # ID must be stable + unique

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            # Fail silently - grouping is a best-effort feature
            pass


class TitleBar(QWidget):
    """
    Reusable title bar widget.
    """

    HEIGHT = 36

    def __init__(
            self,
            window: FramelessWindow,
            title: str = "Frameless App",
            icon_path: str | None = None
    ):
        super().__init__(window)

        self._window = window

        self.setObjectName("Titlebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(self.HEIGHT)

        self.setStyleSheet("""
        #Titlebar {
            border-top: 1px solid #525252;
            border-left: 1px solid #525252;
            border-right: 1px solid #525252;
        }

        #Titlebar QPushButton#CloseButton:hover {
            background: #c42b1c;
            color: white;
        }

        #Titlebar QPushButton#CloseButton:pressed {
            background: #a62216;
            color: white;
        }
        """)
    
        # App Icon
        icon_label = QLabel()
        icon_label.setFixedSize(20,20)
        icon_label.setScaledContents(True)
        icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        pixmap = None

        if isinstance(icon_path, QPixmap):
            pixmap = icon_path
        
        elif isinstance(icon_path, QIcon):
            # Extract a pixmap from the QIcon at the right size
            pixmap = icon_path.pixmap(icon_label.size())
        
        elif isinstance(icon_path, (str, bytes)):
            pixmap = QPixmap(icon_path)

        if pixmap and not pixmap.isNull():
            pixmap = pixmap.scaled(
                icon_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        
        # Title text
        self._title_label = QLabel(title)
        self._title_label.setObjectName("TitleLabel")
        self._title_label.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        btn_min = QPushButton("–")
        btn_max = QPushButton("□")
        btn_close = QPushButton("✕")
        btn_close.setObjectName("CloseButton")

        for btn in (btn_min, btn_max, btn_close):
            btn.setFixedSize(36, 28)
            btn.setFocusPolicy(Qt.NoFocus)

        btn_min.clicked.connect(window.showMinimized)
        btn_max.clicked.connect(self.toggle_maximize)
        btn_close.clicked.connect(self.request_close)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(6)

        layout.addWidget(icon_label)
        layout.addWidget(self._title_label)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_max)
        layout.addWidget(btn_close)

        window.setTitleBar(self)

    # ---------------- TITLEBAR BEHAVIOR ---------------- #

    def request_close(self):
        """
        Native-style close request.
        """
        self._window.closeRequested.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._window.windowHandle().startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()

    def toggle_maximize(self):
        window = self._window
        window.setWindowState(
            Qt.WindowNoState if window.isMaximized() else Qt.WindowMaximized
        )

    # ---------------- SET TITLEBAR NAME ---------------- #

    def setTitle(self, title: str):
        self._title_label.setText(title)


class DialogCode:
    REJECTED = 0
    ACCEPTED = 1

class FramelessDialog(FramelessWindow):
    """
    Reusable frameless dialog container.
    Acts as a drop-in replacement for QDialog.
    """

    finished = Signal(int)

    def __init__(self, parent=None, title="Dialog"):
        app_name = None
        app_icon = None

        if isinstance(parent, FramelessWindow):
            app_name = parent._app_name
            app_icon = parent.windowIcon()

        super().__init__(app_name=app_name, app_icon=app_icon)

        # Dialog State
        self._event_loop: QEventLoop | None = None
        self._result = DialogCode.REJECTED
        self._parent = parent
        self._previous_focus = None

        if parent:
            self.setParent(parent)
            self.setWindowModality(Qt.WindowModal)

        self.setFixedSize(420, 200)

        # Titlebar
        self._titlebar = TitleBar(self, title)
        self.addWidget(self._titlebar)

        # Content Area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)

        self.addWidget(self._content)

    # ---------------- PUBLIC API ---------------- #

    def contentLayout(self):
        return self._content_layout

    # ---------------- EXEC / MODALITY ---------------- #

    def exec(self) -> int:
        if self._event_loop is not None:
            return self._result  # already running

        if self._parent:
            self._parent.setEnabled(False)

        self._previous_focus = QApplication.focusWidget()

        self._event_loop = QEventLoop(self)
        self.finished.connect(self._event_loop.quit)

        self._center_on_parent()
        self.show()
        self.raise_()
        self.activateWindow()

        self._event_loop.exec()

        if self._parent:
            self._parent.setEnabled(True)
            self._parent.activateWindow()

        if self._previous_focus:
            self._previous_focus.setFocus(Qt.OtherFocusReason)

        self._event_loop = None
        return self._result

    # ---------------- DIALOG CONTROL ---------------- #

    def accept(self):
        self.done(DialogCode.ACCEPTED)

    def reject(self):
        self.done(DialogCode.REJECTED)

    def done(self, result: int):
        self._result = result
        self.hide()
        self.finished.emit(result)

    def closeEvent(self, event):
        self.reject()
        event.accept()

    # ---------------- CENTERING ---------------- #

    def _center_on_parent(self):
        """
        Snap dialog to center of parent window or screen.
        """
        if self._parent:
            parent_rect = self._parent.frameGeometry()
            center = parent_rect.center()
        else:
            screen = self.screen() or QApplication.primaryScreen()
            center = screen.availableGeometry().center()

        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    # ---------------- FOCUS TRAP ---------------- #

    def keyPressEvent(self, event):
        """
        Trap Tab / Shift+Tab inside the dialog.
        """
        if event.key() == Qt.Key_Tab:
            self._focus_next(event.modifiers() & Qt.ShiftModifier)
            event.accept()
            return

        super().keyPressEvent(event)

    def _focus_next(self, reverse=False):
        widgets = [
            w for w in self.findChildren(QWidget)
            if w.isVisible() and w.focusPolicy() != Qt.NoFocus
        ]

        if not widgets:
            return

        current = QApplication.focusWidget()
        if current not in widgets:
            widgets[0].setFocus(Qt.TabFocusReason)
            return

        idx = widgets.index(current)
        idx = (idx - 1) if reverse else (idx + 1)
        widgets[idx % len(widgets)].setFocus(Qt.TabFocusReason)
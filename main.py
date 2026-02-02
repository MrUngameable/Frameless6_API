import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from FramelessWindow.frameless_window import FramelessWindow, TitleBar


class MyUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #0F1524;")


def main():
    app = QApplication(sys.argv)

    window = FramelessWindow()

    title_bar = TitleBar(
        window,
        "🚀 My App",
        icon_path=None  # You can pass an icon path here
    )
    content = MyUI()

    window.addWidget(title_bar)
    window.addWidget(content)

    window.resize(1100, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

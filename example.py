import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

from Frameless6_API.frameless6_api import FramelessWindow, TitleBar


class MyWindow(FramelessWindow):
    def __init__(self):
        app_name = "Example"
        app_icon = None

        super().__init__(app_name=app_name, app_icon=app_icon)
        self.setStyleSheet("background: #1c1c1c;")
        self.resize(1100, 700)

        # ---- Titlebar ----
        title_bar = TitleBar(
            window=self,
            title="🚀 My App",
            icon_path=None  # You can pass an icon path here
        )
        self.addWidget(title_bar)

        # ---- Example Content Area ----
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addStretch()     # Push everything up

        self.addWidget(content)


def main():
    app = QApplication(sys.argv)

    window = MyWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

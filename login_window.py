"""
Class LoginWindow - Giao diện đăng nhập
Kế thừa từ QDialog, kiểm tra username và password từ bảng Employees.
"""

import os
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
from PyQt6 import uic


class LoginWindow(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user_info = None  # Lưu thông tin nhân viên sau khi đăng nhập

        # Load UI file
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "login.ui")
        uic.loadUi(ui_path, self)

        # Cấu hình cửa sổ
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Kết nối sự kiện
        self.btnLogin.clicked.connect(self.handle_login)
        self.btnExit.clicked.connect(self.reject)
        self.txtPassword.returnPressed.connect(self.handle_login)
        self.txtUsername.returnPressed.connect(self.txtPassword.setFocus)

        # Focus vào ô username
        self.txtUsername.setFocus()

    def handle_login(self):
        """Xử lý sự kiện đăng nhập."""
        username = self.txtUsername.text().strip()
        password = self.txtPassword.text().strip()

        # Validate input
        if not username:
            self.lblError.setText("⚠️ Vui lòng nhập tên đăng nhập!")
            self.txtUsername.setFocus()
            return

        if not password:
            self.lblError.setText("⚠️ Vui lòng nhập mật khẩu!")
            self.txtPassword.setFocus()
            return

        # Xác thực từ database
        result = self.db.verify_login(username, password)

        if result:
            self.user_info = {
                "id": result[0],
                "username": result[1],
                "fullname": result[2],
                "role": result[3]
            }
            self.accept()  # Đóng dialog với kết quả Accepted
        else:
            self.lblError.setText("❌ Sai tên đăng nhập hoặc mật khẩu!")
            self.txtPassword.clear()
            self.txtPassword.setFocus()

    def get_user_info(self):
        """Trả về thông tin nhân viên đã đăng nhập."""
        return self.user_info

    # ── Cho phép kéo cửa sổ (vì ẩn title bar) ──
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

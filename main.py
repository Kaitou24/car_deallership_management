import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.database_service import DatabaseService
from services.theme_manager import ThemeManager
from login_window import LoginWindow
from views.main_dashboard import MainDashboard

def main():
    # Tạo ứng dụng
    app = QApplication(sys.argv)
    app.setApplicationName("Quản Lý Đại Lý Xe Hơi")

    # Đặt font Segoe UI toàn cục
    app.setFont(QFont("Segoe UI", 10))

    # Nạp giao diện theo tùy chọn người dùng (Sáng / Tối)
    current_theme = ThemeManager.get_current_theme()
    ThemeManager.apply_theme(app, current_theme)

    # Khởi tạo database (Singleton)
    db = DatabaseService.get_instance()

    # Vòng lặp đăng nhập → sử dụng → đăng xuất → đăng nhập lại
    while True:
        # Hiển thị cửa sổ đăng nhập
        login = LoginWindow(db)
        result = login.exec()

        if result != QDialog.DialogCode.Accepted:
            # Người dùng đóng cửa sổ đăng nhập → thoát app
            break

        # Lấy thông tin nhân viên đã đăng nhập
        user_info = login.get_user_info()

        # Hiển thị cửa sổ chính (MainDashboard với Sidebar)
        main_window = MainDashboard(db, user_info)
        main_window.show()

        # Chạy event loop cho MainWindow
        app.exec()

        # Khi MainWindow đóng (logout), quay lại vòng lặp hiển thị Login

    # Đóng database
    db.close()
    sys.exit(0)


if __name__ == "__main__":
    main()

"""
Class MainWindow - Giao diện chính
Điều khiển toàn bộ tương tác: hiển thị danh sách xe, thêm/sửa/xóa/bán xe, xem hóa đơn.
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QTableWidgetItem, QMessageBox,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6 import uic

from database import Database
from car import Car
from sale_logic import SaleLogic


class AddCarDialog(QDialog):
    """Dialog thêm / sửa xe."""

    def __init__(self, parent=None, car=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "add_car_dialog.ui")
        uic.loadUi(ui_path, self)

        self.car = car  # None = thêm mới, có giá trị = sửa

        # Kết nối sự kiện
        self.btnSave.clicked.connect(self.handle_save)
        self.btnCancel.clicked.connect(self.reject)

        # Nếu đang sửa xe, điền thông tin cũ
        if self.car:
            self.setWindowTitle("Sửa Thông Tin Xe")
            self.lblDialogTitle.setText("✏️ SỬA THÔNG TIN XE")
            self.cmbBrand.setCurrentText(car.brand)
            self.txtModel.setText(car.model)
            self.spnYear.setValue(car.year)
            self.spnPrice.setValue(car.price)

    def handle_save(self):
        """Xử lý lưu thông tin xe."""
        brand = self.cmbBrand.currentText().strip()
        model = self.txtModel.text().strip()
        year = self.spnYear.value()
        price = self.spnPrice.value()

        # Validate
        if not brand:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn hoặc nhập hãng xe!")
            return
        if not model:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập model xe!")
            self.txtModel.setFocus()
            return
        if price <= 0:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập giá xe hợp lệ!")
            return

        # Tạo / cập nhật đối tượng Car
        if self.car:
            self.car.brand = brand
            self.car.model = model
            self.car.year = year
            self.car.price = price
        else:
            self.car = Car(model=model, brand=brand, year=year, price=price)

        self.accept()

    def get_car(self):
        """Trả về đối tượng Car đã nhập."""
        return self.car


class SellCarDialog(QDialog):
    """Dialog bán xe - tạo hóa đơn."""

    def __init__(self, parent=None, car=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "sell_car_dialog.ui")
        uic.loadUi(ui_path, self)

        self.car = car
        self.sale_logic = SaleLogic()

        # Hiển thị thông tin xe
        if car:
            self.lblCarInfo.setText(f"🚗 {car.brand} {car.model} ({car.year})")
            self.lblCarPrice.setText(f"Giá gốc: {SaleLogic.format_currency(car.price)}")

        # Kết nối sự kiện
        self.btnConfirm.clicked.connect(self.handle_confirm)
        self.btnCancel.clicked.connect(self.reject)

        # Tự động tính tổng khi thay đổi thuế/giảm giá
        self.spnTax.valueChanged.connect(self.update_total)
        self.spnDiscount.valueChanged.connect(self.update_total)

        # Tính tổng ban đầu
        self.update_total()

    def update_total(self):
        """Cập nhật tổng tiền khi thay đổi thuế hoặc giảm giá."""
        if not self.car:
            return
        price = self.car.price
        tax = self.spnTax.value()
        discount = self.spnDiscount.value()
        total = SaleLogic.calculate_total(price, tax, discount)
        self.lblTotal.setText(SaleLogic.format_currency(total))

    def handle_confirm(self):
        """Xử lý xác nhận bán xe."""
        customer_name = self.txtCustomer.text().strip()

        # Validate
        is_valid, error_msg = SaleLogic.validate_sale(self.car, customer_name)
        if not is_valid:
            QMessageBox.warning(self, "Không thể bán", error_msg)
            return

        # Xác nhận lần cuối
        total = SaleLogic.calculate_total(
            self.car.price, self.spnTax.value(), self.spnDiscount.value()
        )
        reply = QMessageBox.question(
            self, "Xác nhận bán xe",
            f"Bán xe {self.car.brand} {self.car.model} cho {customer_name}\n"
            f"Tổng thanh toán: {SaleLogic.format_currency(total)}\n\n"
            f"Xác nhận?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_sale_data(self):
        """Trả về dữ liệu bán hàng."""
        total = SaleLogic.calculate_total(
            self.car.price, self.spnTax.value(), self.spnDiscount.value()
        )
        return {
            "car_id": self.car.id,
            "customer_name": self.txtCustomer.text().strip(),
            "price": self.car.price,
            "tax": self.spnTax.value(),
            "discount": self.spnDiscount.value(),
            "total": total,
            "sale_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }


class MainWindow(QMainWindow):
    """Giao diện chính - Quản lý đại lý xe hơi."""

    def __init__(self, db: Database, user_info: dict):
        super().__init__()
        self.db = db
        self.user_info = user_info

        # Load UI file
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "main_window.ui")
        uic.loadUi(ui_path, self)

        # Cấu hình cửa sổ
        self.setWindowTitle(f"Quản Lý Đại Lý Xe Hơi - {user_info['fullname']}")

        # Hiển thị thông tin nhân viên
        self.lblUserInfo.setText(f"👤 {user_info['fullname']} ({user_info['role']})")

        # Cấu hình bảng
        self._setup_table()

        # Kết nối sự kiện
        self._connect_events()

        # Load dữ liệu
        self.load_cars()
        self.update_stats()

        # Status bar
        self.statusBar.showMessage("✅ Sẵn sàng | Đăng nhập: " + user_info['fullname'])

    def _setup_table(self):
        """Cấu hình QTableWidget."""
        table = self.tableCars
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ID", "Hãng Xe", "Model", "Năm SX", "Giá (VNĐ)", "Trạng Thái"])

        # Điều chỉnh độ rộng cột
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(0, 60)
        table.setColumnWidth(3, 80)
        table.setColumnWidth(5, 120)

        # Chọn cả dòng, chỉ 1 dòng
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Đường kẻ xen kẽ
        table.setAlternatingRowColors(True)

        # Chiều cao dòng
        table.verticalHeader().setDefaultSectionSize(42)
        table.verticalHeader().setVisible(False)

    def _connect_events(self):
        """Kết nối tất cả sự kiện nút bấm."""
        self.btnAddCar.clicked.connect(self.add_car)
        self.btnEditCar.clicked.connect(self.edit_car)
        self.btnDeleteCar.clicked.connect(self.delete_car)
        self.btnSellCar.clicked.connect(self.sell_car)
        self.btnInvoices.clicked.connect(self.show_invoices)
        self.btnLogout.clicked.connect(self.logout)

        # Tìm kiếm
        self.txtSearch.textChanged.connect(self.search_cars)
        self.cmbFilter.currentTextChanged.connect(self.search_cars)

        # Double-click vào bảng để sửa xe
        self.tableCars.doubleClicked.connect(self.edit_car)

    # ──────────────── Load & Display Data ────────────────

    def load_cars(self):
        """Tải và hiển thị danh sách xe lên bảng."""
        cars = self.db.get_all_cars()
        self._display_cars(cars)

    def _display_cars(self, cars):
        """Hiển thị danh sách Car lên QTableWidget."""
        table = self.tableCars
        table.setRowCount(0)

        for car in cars:
            row = table.rowCount()
            table.insertRow(row)

            # ID
            id_item = QTableWidgetItem(str(car.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, id_item)

            # Hãng xe
            table.setItem(row, 1, QTableWidgetItem(car.brand))

            # Model
            table.setItem(row, 2, QTableWidgetItem(car.model))

            # Năm SX
            year_item = QTableWidgetItem(str(car.year))
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 3, year_item)

            # Giá
            price_item = QTableWidgetItem(SaleLogic.format_currency(car.price))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, price_item)

            # Trạng thái
            status_item = QTableWidgetItem(car.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if car.status == "Đã bán":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            table.setItem(row, 5, status_item)

    def update_stats(self):
        """Cập nhật thống kê trên cards."""
        stats = self.db.get_stats()
        self.lblStatTotal.setText(str(stats["total"]))
        self.lblStatAvailable.setText(str(stats["available"]))
        self.lblStatSold.setText(str(stats["sold"]))

    def search_cars(self):
        """Tìm kiếm và lọc xe."""
        keyword = self.txtSearch.text().strip()
        status_filter = self.cmbFilter.currentText()

        if keyword or status_filter != "Tất cả":
            cars = self.db.search_cars(keyword, status_filter)
        else:
            cars = self.db.get_all_cars()

        self._display_cars(cars)

    # ──────────────── CRUD Operations ────────────────

    def _get_selected_car_id(self):
        """Lấy ID xe đang chọn trong bảng."""
        selected = self.tableCars.selectedItems()
        if not selected:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn một xe trong bảng!")
            return None
        row = selected[0].row()
        car_id = int(self.tableCars.item(row, 0).text())
        return car_id

    def add_car(self):
        """Mở dialog thêm xe mới."""
        dialog = AddCarDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            car = dialog.get_car()
            self.db.add_car(car)
            self.load_cars()
            self.update_stats()
            self.statusBar.showMessage(f"✅ Đã thêm xe: {car.brand} {car.model}", 3000)

    def edit_car(self):
        """Mở dialog sửa xe đang chọn."""
        car_id = self._get_selected_car_id()
        if car_id is None:
            return

        car = self.db.get_car_by_id(car_id)
        if not car:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy xe này!")
            return

        dialog = AddCarDialog(self, car)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_car = dialog.get_car()
            self.db.update_car(updated_car)
            self.load_cars()
            self.update_stats()
            self.statusBar.showMessage(f"✅ Đã cập nhật xe: {updated_car.brand} {updated_car.model}", 3000)

    def delete_car(self):
        """Xóa xe đang chọn."""
        car_id = self._get_selected_car_id()
        if car_id is None:
            return

        car = self.db.get_car_by_id(car_id)
        if not car:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy xe này!")
            return

        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa xe:\n{car.brand} {car.model} ({car.year})?\n\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_car(car_id)
            self.load_cars()
            self.update_stats()
            self.statusBar.showMessage(f"🗑️ Đã xóa xe: {car.brand} {car.model}", 3000)

    def sell_car(self):
        """Mở dialog bán xe."""
        car_id = self._get_selected_car_id()
        if car_id is None:
            return

        car = self.db.get_car_by_id(car_id)
        if not car:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy xe này!")
            return

        if not SaleLogic.is_available(car):
            QMessageBox.warning(self, "Không thể bán", "Xe này đã được bán rồi!")
            return

        dialog = SellCarDialog(self, car)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sale_data = dialog.get_sale_data()

            # Lưu hóa đơn
            self.db.add_invoice(
                car_id=sale_data["car_id"],
                employee_id=self.user_info["id"],
                customer_name=sale_data["customer_name"],
                sale_date=sale_data["sale_date"],
                price=sale_data["price"],
                tax=sale_data["tax"],
                discount=sale_data["discount"],
                total=sale_data["total"]
            )

            # Cập nhật trạng thái xe
            self.db.update_status(car_id, "Đã bán")

            self.load_cars()
            self.update_stats()
            self.statusBar.showMessage(
                f"💰 Đã bán xe {car.brand} {car.model} - Tổng: {SaleLogic.format_currency(sale_data['total'])}",
                5000
            )

    # ──────────────── Invoices ────────────────

    def show_invoices(self):
        """Hiển thị danh sách hóa đơn trong dialog."""
        invoices = self.db.get_all_invoices()

        if not invoices:
            QMessageBox.information(self, "Hóa đơn", "Chưa có hóa đơn nào!")
            return

        # Tạo dialog hiển thị hóa đơn
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("📄 Danh Sách Hóa Đơn")
        dialog.setMinimumSize(900, 500)

        layout = QVBoxLayout(dialog)

        title = QLabel("📄 DANH SÁCH HÓA ĐƠN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a237e; padding: 10px;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Mã HĐ", "Xe", "Nhân viên", "Khách hàng",
            "Ngày bán", "Giá gốc", "Thuế (%)", "Giảm giá", "Tổng tiền"
        ])

        header = table.horizontalHeader()
        for i in range(9):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40)

        for inv in invoices:
            row = table.rowCount()
            table.insertRow(row)
            # inv = (id, car_name, employee_name, customer_name, sale_date, price, tax, discount, total)
            items = [
                str(inv[0]),
                inv[1],
                inv[2],
                inv[3],
                inv[4],
                SaleLogic.format_currency(inv[5]),
                f"{inv[6]}%",
                SaleLogic.format_currency(inv[7]),
                SaleLogic.format_currency(inv[8])
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col in (0, 4, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col in (5, 7, 8):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, item)

        layout.addWidget(table)
        dialog.exec()

    # ──────────────── Logout ────────────────

    def logout(self):
        """Đăng xuất - đóng MainWindow."""
        reply = QMessageBox.question(
            self, "Đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

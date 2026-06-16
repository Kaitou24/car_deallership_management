"""
Class SaleLogic - Xử lý bán hàng
Chứa các công thức tính toán, đảm bảo code giao diện không bị rối bởi logic toán học.
Công thức: Total = Price × (1 + Tax) - Discount
"""


class SaleLogic:

    @staticmethod
    def calculate_total(price, tax_rate, discount):
        """
        Tính tổng tiền phải thanh toán.
        - price: giá xe gốc
        - tax_rate: thuế (dạng %, ví dụ 10 = 10%)
        - discount: số tiền giảm giá
        Công thức: Total = Price × (1 + Tax/100) - Discount
        """
        tax_decimal = tax_rate / 100.0
        total = price * (1 + tax_decimal) - discount
        return max(total, 0)  # Không cho phép tổng âm

    @staticmethod
    def is_available(car):
        """Kiểm tra xe còn trong kho không."""
        return car.status == "Còn hàng"

    @staticmethod
    def validate_sale(car, customer_name):
        """
        Validate dữ liệu trước khi tạo hóa đơn.
        Trả về (True, "") nếu hợp lệ hoặc (False, "Lý do lỗi").
        """
        if not car:
            return False, "Không tìm thấy thông tin xe."

        if not SaleLogic.is_available(car):
            return False, "Xe này đã được bán, không thể tạo hóa đơn."

        if not customer_name or not customer_name.strip():
            return False, "Vui lòng nhập tên khách hàng."

        return True, ""

    @staticmethod
    def format_currency(amount):
        """Định dạng số tiền theo kiểu Việt Nam. VD: 1,500,000,000 VNĐ"""
        return f"{amount:,.0f} VNĐ"

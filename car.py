"""
Class Car - Thực thể Xe
Đóng gói thông tin của một chiếc xe, giúp việc truyền dữ liệu
giữa giao diện và database sạch sẽ hơn.
"""


class Car:
    def __init__(self, id=None, model="", brand="", year=2024, price=0.0, status="Còn hàng"):
        self.id = id
        self.model = model
        self.brand = brand
        self.year = year
        self.price = price
        self.status = status

    def to_dict(self):
        """Chuyển đối tượng Car thành dictionary."""
        return {
            "id": self.id,
            "model": self.model,
            "brand": self.brand,
            "year": self.year,
            "price": self.price,
            "status": self.status
        }

    @staticmethod
    def from_row(row):
        """Tạo đối tượng Car từ một dòng dữ liệu SQLite (tuple)."""
        return Car(
            id=row[0],
            model=row[1],
            brand=row[2],
            year=row[3],
            price=row[4],
            status=row[5]
        )

    def __repr__(self):
        return f"Car(id={self.id}, brand='{self.brand}', model='{self.model}', year={self.year}, price={self.price}, status='{self.status}')"

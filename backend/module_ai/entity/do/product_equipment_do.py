from sqlalchemy import String, BigInteger, Column

from config.database import Base


class ProductEquipmentInfo(Base):
    """
    产品组件表
    """

    __tablename__ = 'product_equipment_info'
    __table_args__ = {'comment': '产品组件表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='id唯一标识')
    product_name = Column(String(255), nullable=False, comment='备件名称')
    product_no = Column(String(255), nullable=False, comment='备件号')
    price_including_tax = Column(String(255), nullable=False, comment='含税价')
    purchase_price = Column(String(255), nullable=False, comment='进货价')




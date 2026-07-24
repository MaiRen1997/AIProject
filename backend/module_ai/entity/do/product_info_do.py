from sqlalchemy import String, BigInteger, Column

from config.database import Base


class ProductModelInfo(Base):
    """
    产品组件关联表
    """

    __tablename__ = 'product_model_info'
    __table_args__ = {'comment': '产品组件关联表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='id唯一标识')
    product_name = Column(String(255), nullable=False, comment='产品名称')
    product_no = Column(String(255), nullable=False, comment='产品号')
    equipment_id = Column(String(255), nullable=False, comment='组成组件号')
    relation_eqp_id = Column(String(255), nullable=True, comment='强关联组件号(只能是这个配件)')





from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank




class Product_infoModel(BaseModel):
    """
    产品组件关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='id唯一标识')
    product_name: str | None = Field(default=None, description='产品名称')
    product_no: str | None = Field(default=None, description='产品号')
    equipment_id: str | None = Field(default=None, description='组成组件号')
    relation_eqp_id: str | None = Field(default=None, description='强关联组件号(只能是这个配件)')

    @NotBlank(field_name='product_name', message='产品名称不能为空')
    def get_product_name(self) -> str | None:
        return self.product_name

    @NotBlank(field_name='product_no', message='产品号不能为空')
    def get_product_no(self) -> str | None:
        return self.product_no

    @NotBlank(field_name='equipment_id', message='组成组件号不能为空')
    def get_equipment_id(self) -> str | None:
        return self.equipment_id


    def validate_fields(self) -> None:
        self.get_product_name()
        self.get_product_no()
        self.get_equipment_id()




class Product_infoQueryModel(Product_infoModel):
    """
    产品组件关联不分页查询模型
    """
    pass


class Product_infoPageQueryModel(Product_infoQueryModel):
    """
    产品组件关联分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProduct_infoModel(BaseModel):
    """
    删除产品组件关联模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的id唯一标识')

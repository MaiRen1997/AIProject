
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank




class Product_equipmentModel(BaseModel):
    """
    产品组件表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='id唯一标识')
    product_name: str | None = Field(default=None, description='备件名称')
    product_no: str | None = Field(default=None, description='备件号')
    price_including_tax: str | None = Field(default=None, description='含税价')
    purchase_price: str | None = Field(default=None, description='进货价')

    @NotBlank(field_name='product_name', message='备件名称不能为空')
    def get_product_name(self) -> str | None:
        return self.product_name

    @NotBlank(field_name='product_no', message='备件号不能为空')
    def get_product_no(self) -> str | None:
        return self.product_no

    @NotBlank(field_name='price_including_tax', message='含税价不能为空')
    def get_price_including_tax(self) -> str | None:
        return self.price_including_tax

    @NotBlank(field_name='purchase_price', message='进货价不能为空')
    def get_purchase_price(self) -> str | None:
        return self.purchase_price

    def validate_fields(self) -> None:
        self.get_product_name()
        self.get_product_no()
        self.get_price_including_tax()
        self.get_purchase_price()




class Product_equipmentQueryModel(Product_equipmentModel):
    """
    产品组件不分页查询模型
    """
    pass


class Product_equipmentPageQueryModel(Product_equipmentQueryModel):
    """
    产品组件分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProduct_equipmentModel(BaseModel):
    """
    删除产品组件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的id唯一标识')

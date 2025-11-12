import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional

from app.core.base_schema import BaseSchema


class DictTypeCreateSchema(BaseModel):
    """
    字典类型表对应pydantic模型
    """

    dict_name: str = Field(..., min_length=1, max_length=100, description='字典名称')
    dict_type: str = Field(..., min_length=1, max_length=100, description='字典类型')
    status: Optional[bool] = Field(default=None, description='状态（1正常 0停用）')
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @field_validator('dict_name')
    def validate_dict_name(cls, value: str):
        if not value or value.strip() == '':
            raise ValueError('字典名称不能为空')
        return value

    @field_validator('dict_type')
    def validate_dict_type(cls, value: str):
        if not value or value.strip() == '':
            raise ValueError('字典类型不能为空')
        regexp = r'^[a-z][a-z0-9_]*$'
        if not re.match(regexp, value):
            raise ValueError('字典类型必须以字母开头，且只能为（小写字母，数字，下滑线）')
        return value


class DictTypeUpdateSchema(DictTypeCreateSchema):
    """字典类型更新模型"""
    ...


class DictTypeOutSchema(DictTypeCreateSchema, BaseSchema):
    """字典类型响应模型"""
    model_config = ConfigDict(from_attributes=True)


class DictDataCreateSchema(BaseModel):
    """
    字典数据表对应pydantic模型
    """
    dict_sort: int = Field(..., ge=1, description='字典排序')
    dict_label: str = Field(..., max_length=100, description='字典标签')
    dict_value: str = Field(..., max_length=100, description='字典键值')
    dict_type: str = Field(..., max_length=100, description='字典类型')
    css_class: Optional[str] = Field(default=None, max_length=100, description='样式属性（其他样式扩展）')
    list_class: Optional[str] = Field(default=None, description='表格回显样式')
    is_default: Optional[bool] = Field(default=None, description='是否默认（Y是 N否）')
    status: Optional[bool] = Field(default=None, description='状态（1正常 0停用）')
    description: Optional[str] = Field(default=None, max_length=255, description="描述")
    
    @model_validator(mode='after')
    def validate_after(self):
        if self.dict_label is None or self.dict_label.strip() == '':
            raise ValueError('字典标签不能为空')
        if self.dict_value is None or self.dict_value.strip() == '':
            raise ValueError('字典键值不能为空')
        if self.dict_type is None or self.dict_type.strip() == '':
            raise ValueError('字典类型不能为空')
        return self


class DictDataUpdateSchema(DictDataCreateSchema):
    """字典数据更新模型"""
    ...


class DictDataOutSchema(DictDataCreateSchema, BaseSchema):
    """字典数据响应模型"""
    model_config = ConfigDict(from_attributes=True)

# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseSchema
from app.core.validator import DateTimeStr

class PositionCreateSchema(BaseModel):
    """岗位创建模型"""
    name: str = Field(..., max_length=40, description="岗位名称")
    order: Optional[int] = Field(default=1, ge=1, description='显示排序')
    status: bool = Field(default=True, description="是否启用(True:启用 False:禁用)")
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @field_validator('name')
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('岗位名称不能为空')
        return v


class PositionUpdateSchema(PositionCreateSchema):
    """岗位更新模型"""
    ...


class PositionOutSchema(PositionCreateSchema, BaseSchema):
    """岗位信息响应模型"""
    model_config = ConfigDict(from_attributes=True)
    ...

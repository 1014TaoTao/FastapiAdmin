# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.base_schema import BaseSchema
from urllib.parse import urlparse


class ApplicationCreateSchema(BaseModel):
    """应用创建模型"""
    name: str = Field(..., max_length=64, description='应用名称')
    access_url: str = Field(..., max_length=255, description="访问地址")
    icon_url: Optional[str] = Field(None, max_length=300, description="应用图标URL")
    status: bool = Field(True, description="是否启用(True:启用 False:禁用)")
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @field_validator('name')
    @classmethod
    def _validate_name_length(cls, v: str) -> str:
        if len(v) > 64:
            raise ValueError('应用名称长度不能超过64字符')
        return v

    @field_validator('access_url')
    @classmethod
    def _validate_access_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('访问地址不能为空')
        parsed = urlparse(v)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError('访问地址必须为 http/https URL')
        return v

    @field_validator('icon_url')
    @classmethod
    def _validate_icon_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        parsed = urlparse(v)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError('应用图标URL必须为 http/https URL')
        return v


class ApplicationUpdateSchema(ApplicationCreateSchema):
    """应用更新模型"""
    ...


class ApplicationOutSchema(ApplicationCreateSchema, BaseSchema):
    """应用响应模型"""
    model_config = ConfigDict(from_attributes=True)

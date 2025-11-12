# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseSchema


class NoticeCreateSchema(BaseModel):
    """公告通知创建模型"""
    notice_title: str = Field(..., max_length=50, description='公告标题')
    notice_type: str = Field(..., description='公告类型（1通知 2公告）')
    notice_content: str = Field(..., description='公告内容')
    status: bool = Field(default=True, description="是否启用(True:启用 False:禁用)")
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @field_validator("notice_type")
    @classmethod
    def _validate_notice_type(cls, value: str):
        if value not in {"1", "2"}:
            raise ValueError("公告类型仅支持 '1'(通知) 或 '2'(公告)")
        return value

    @model_validator(mode='after')
    def _validate_after(self):
        if not self.notice_title.strip():
            raise ValueError("公告标题不能为空")
        if not self.notice_content.strip():
            raise ValueError("公告内容不能为空")
        return self


class NoticeUpdateSchema(NoticeCreateSchema):
    """公告通知更新模型"""
    ...


class NoticeOutSchema(NoticeCreateSchema, BaseSchema):
    """公告通知响应模型"""
    model_config = ConfigDict(from_attributes=True)

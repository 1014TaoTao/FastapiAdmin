# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.base_schema import BaseSchema
import re


class OperationLogCreateSchema(BaseModel):
    """日志创建模型"""
    type: Optional[int] = Field(default=None, description="日志类型(1登录日志 2操作日志)")
    request_path: Optional[str] = Field(default=None, description="请求路径")
    request_method: Optional[str] = Field(default=None, description="请求方法")
    request_payload: Optional[str] = Field(default=None, description="请求负载")
    request_ip: Optional[str] = Field(default=None, description="请求 IP 地址")
    login_location: Optional[str] = Field(default=None, description="登录位置")
    request_os: Optional[str] = Field(default=None, description="请求操作系统")
    request_browser: Optional[str] = Field(default=None, description="请求浏览器")
    response_code: Optional[int] = Field(default=None, description="响应状态码")
    response_json: Optional[str] = Field(default=None, description="响应 JSON 数据")
    process_time: Optional[str] = Field(default=None, description="处理时间")
    description: Optional[str] = Field(default=None, max_length=255, description="描述")
    creator_id: Optional[int] = Field(default=None, description="创建人ID")

    @field_validator("type")
    @classmethod
    def _validate_type(cls, value: Optional[int]):
        if value is None:
            return value
        if value not in {1, 2}:
            raise ValueError("日志类型仅支持 1(登录) 或 2(操作)")
        return value

    @field_validator("request_method")
    @classmethod
    def _validate_method(cls, value: Optional[str]):
        if value is None:
            return value
        allowed = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        if value.upper() not in allowed:
            raise ValueError(f"请求方法必须为 {', '.join(sorted(allowed))}")
        return value.upper()

    @field_validator("request_ip")
    @classmethod
    def _validate_ip(cls, value: Optional[str]):
        if value is None or value == "":
            return value
        ipv4 = r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$"
        ipv6 = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        if not re.match(ipv4, value) and not re.match(ipv6, value):
            raise ValueError("请求IP必须为有效的IPv4或IPv6地址")
        return value


class OperationLogOutSchema(OperationLogCreateSchema, BaseSchema):
    """日志响应模型"""
    model_config = ConfigDict(from_attributes=True)

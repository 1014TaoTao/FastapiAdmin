# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

from app.core.validator import DateTimeStr, mobile_validator
from app.core.base_schema import BaseSchema, CommonSchema
from app.api.v1.module_system.role.schema import RoleOutSchema
from urllib.parse import urlparse

class CurrentUserUpdateSchema(BaseModel):
    """基础用户信息"""
    name: Optional[str] = Field(default=None, max_length=32, description="名称")
    mobile: Optional[str] = Field(default=None, description="手机号")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    gender: Optional[str] = Field(default=None, description="性别")
    avatar: Optional[str] = Field(default=None, description="头像")

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: Optional[str]):
        return mobile_validator(value)

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, value: Optional[str]):
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return value
        raise ValueError("头像地址需为有效的HTTP/HTTPS URL")


class UserRegisterSchema(BaseModel):
    """注册"""
    name: Optional[str] = Field(default=None, max_length=32, description="名称")
    mobile: Optional[str] = Field(default=None, description="手机号")
    username: str = Field(..., max_length=32, description="账号")
    password: str = Field(..., max_length=128, description="密码哈希值")
    role_ids: Optional[List[int]] = Field(default=[1], description='角色ID')
    creator_id: Optional[int] = Field(default=1, description='创建人ID')
    description: Optional[str] = Field(default=None, max_length=255, description="备注")

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: Optional[str]):
        return mobile_validator(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        v = value.strip()
        if not v:
            raise ValueError("账号不能为空")
        # 字母开头，允许字母数字_.-
        import re
        if not re.match(r"^[A-Za-z][A-Za-z0-9_.-]{2,31}$", v):
            raise ValueError("账号需字母开头，3-32位，仅含字母/数字/_ . -")
        return v


class UserForgetPasswordSchema(BaseModel):
    """忘记密码"""
    username: str = Field(..., max_length=32, description="用户名")
    new_password: str = Field(..., max_length=128, description="新密码")
    mobile: Optional[str] = Field(default=None, description="手机号")
    
    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: Optional[str]):
        return mobile_validator(value)


class UserChangePasswordSchema(BaseModel):
    """修改密码"""
    old_password: str = Field(..., max_length=128, description="旧密码")
    new_password: str = Field(..., max_length=128, description="新密码")


class ResetPasswordSchema(BaseModel):
    """重置密码"""
    id: int = Field(..., description="主键ID")
    password: str = Field(..., min_length=6, max_length=128, description="新密码")


class UserCreateSchema(CurrentUserUpdateSchema):
    """新增"""
    model_config = ConfigDict(from_attributes=True)
    
    username: Optional[str] = Field(default=None, max_length=32, description="用户名")
    password: Optional[str] = Field(default=None, max_length=128, description="密码哈希值")
    status: bool = Field(default=True, description="是否可用")
    is_superuser: bool = Field(default=False, description="是否超管")
    description: Optional[str] = Field(default=None, max_length=255, description="备注")
    
    dept_id: Optional[int] = Field(default=None, description='部门ID')
    role_ids: Optional[List[int]] = Field(default=[], description='角色ID')
    position_ids: Optional[List[int]] = Field(default=[], description='岗位ID')


class UserUpdateSchema(UserCreateSchema):
    """更新"""
    model_config = ConfigDict(from_attributes=True)

    last_login: Optional[DateTimeStr] = Field(default=None, description="最后登录时间")


class UserOutSchema(UserUpdateSchema, BaseSchema):
    """响应"""
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)
    
    dept_name: Optional[str] = Field(default=None, description='部门名称')
    dept: Optional[CommonSchema] = Field(default=None, description='部门')
    roles: Optional[List[RoleOutSchema]] = Field(default=[], description='角色')
    positions: Optional[List[CommonSchema]] = Field(default=[], description='岗位')

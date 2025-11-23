# -*- coding: utf-8 -*-

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class ParamsModel(ModelMixin):
    """
    参数配置表
    
    参数配置隔离策略:
    =============
    - 系统级参数(tenant_id=NULL):
      * 平台级配置参数,影响所有租户
      * config_type=True表示系统内置,不可删除
      * 如:系统名称、Logo、邮件配置等
      
    - 租户级参数(tenant_id>1):
      * 租户自定义配置参数,仅本租户生效
      * config_type=False表示可自定义
      * 如:租户LOGO、业务配置等
      
    - 不需要customer_id:
      * 参数是租户级配置,不属于客户
    
    用于存储系统配置参数，包括：
    - 系统级别参数
    - 租户级别参数
    - 配置项的名称、键、值和类型等信息
    """
    __tablename__: str = "system_param"
    __table_args__: dict[str, str] = ({'comment': '系统参数表'})

    config_name: Mapped[str] = mapped_column(String(500), nullable=False, comment='参数名称')
    config_key: Mapped[str] = mapped_column(String(500), nullable=False, comment='参数键名')
    config_value: Mapped[str | None] = mapped_column(String(500), comment='参数键值')
    config_type: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True, comment="系统内置(True:是 False:否)")

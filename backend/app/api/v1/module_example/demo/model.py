# -*- coding: utf-8 -*-

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin, TenantMixin, CustomerMixin


class DemoModel(ModelMixin, UserMixin, TenantMixin, CustomerMixin):
    """
    示例表
    
    数据隔离策略:
    - 租户级示例: tenant_id必填, customer_id=NULL
    - 客户级示例: tenant_id必填, customer_id>0
    
    根据业务需求,此示例表支持客户级数据隔离
    """
    __tablename__: str = 'gen_demo'
    __table_args__: dict[str, str] = ({'comment': '示例表'})
    __loader_options__: list[str] = ["created_by", "updated_by", "tenant", "customer"]

    name: Mapped[str | None] = mapped_column(String(64), nullable=True, default='', comment='名称')

# -*- coding: utf-8 -*-

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class DictTypeModel(ModelMixin):
    """
    字典类型表
    """
    __tablename__: str = "system_dict_type"
    __table_args__: dict[str, str] = ({'comment': '字典类型表'})

    dict_name: Mapped[str] = mapped_column(String(255), nullable=False, comment='字典名称')
    dict_type: Mapped[str] = mapped_column(String(255), nullable=False, comment='字典类型')


class DictDataModel(ModelMixin):
    """
    字典数据表
    """
    __tablename__: str = "system_dict_data"
    __table_args__: dict[str, str] = ({'comment': '字典数据表'})
    
    dict_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='字典排序')
    dict_label: Mapped[str] = mapped_column(String(255), nullable=False, comment='字典标签')
    dict_value: Mapped[str] = mapped_column(String(255), nullable=False, comment='字典键值')
    css_class: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='样式属性（其他样式扩展）')
    list_class: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='表格回显样式')
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment='是否默认（True是 False否）')
    dict_type: Mapped[str] = mapped_column(String(255), nullable=True, comment='字典类型')

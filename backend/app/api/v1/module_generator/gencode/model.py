# -*- coding: utf-8 -*-

from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.setting import settings
from app.core.base_model import CreatorMixin
from app.utils.common_util import SqlalchemyUtil


class GenTableModel(CreatorMixin):
    """
    代码生成表
    """
    __tablename__ = 'gen_table'
    __table_args__ = ({'comment': '代码生成表'})
    __loader_options__ = ["columns", "creator"]

    table_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default='', comment='表名称')
    table_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default='', comment='表描述')
    sub_table_name : Mapped[Optional[str]] = mapped_column(String(64), nullable=True, server_default=SqlalchemyUtil.get_server_default_null(settings.DATABASE_TYPE), comment='关联子表的表名',)
    sub_table_fk_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, server_default=SqlalchemyUtil.get_server_default_null(settings.DATABASE_TYPE), comment='子表关联的外键名',)
    class_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default='', comment='实体类名称')
    package_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment='生成包路径')
    module_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment='生成模块名')
    business_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment='生成业务名')
    function_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment='生成功能名')
    gen_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, default='0', comment='生成代码方式（0zip压缩包 1生成项目路径）')
    options: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, comment='其它生成选项')
    
    # 关系定义
    columns: Mapped[List['GenTableColumnModel']] = relationship(
        'GenTableColumnModel', 
        order_by='GenTableColumnModel.sort', 
        back_populates='tables',
        cascade='all, delete-orphan'
    )


class GenTableColumnModel(CreatorMixin):
    """
    代码生成表字段
    """
    __tablename__ = 'gen_table_column'
    __table_args__ = ({'comment': '代码生成表字段'})
    __loader_options__ = ["tables", "creator"]

    column_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment='列名称')
    column_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment='列描述')
    column_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment='列类型')
    python_type: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment='PYTHON类型')
    python_field: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment='PYTHON字段名')
    is_pk: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否主键（1是）')
    is_increment: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否自增（1是）')
    is_required: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否必填（1是）')
    is_unique: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否唯一（1是）')
    is_insert: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否为插入字段（1是）')
    is_edit: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否编辑字段（1是）')
    is_list: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否列表字段（1是）')
    is_query: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment='是否查询字段（1是）')
    query_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default='EQ', comment='查询方式（等于、不等于、大于、小于、范围）')
    html_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment='显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）')
    dict_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default='', comment='字典类型')
    sort: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment='排序')

    # 外键关系
    table_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey('gen_table.id', ondelete='CASCADE'), 
        nullable=True, 
        comment='归属表编号'
    )
    
    # 关系定义
    tables: Mapped['GenTableModel'] = relationship(
        'GenTableModel', 
        back_populates='columns'
    )
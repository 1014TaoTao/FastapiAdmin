# -*- coding:utf-8 -*-

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.base_schema import BaseSchema


class GenTableOptionSchema(BaseModel):
    """代码生成表的附加选项（存入`options`字段的JSON）。
    - parent_menu_id：菜单归属；树模板依赖。
    - tree_*：树形结构必需的编码/父编码/名称字段。
    """

    model_config = ConfigDict(from_attributes=True)

    parent_menu_id: Optional[int] = Field(default=None, description='所属父级分类')



class GenDBTableSchema(BaseModel):
    """数据库中的表信息（跨方言统一结构）。
    - 供“导入表结构”与“同步结构”环节使用。
    """

    model_config = ConfigDict(from_attributes=True)

    database_name: Optional[str] = Field(default=None, description='数据库名称')
    table_name: Optional[str] = Field(default=None, description='表名称')
    table_type: Optional[str] = Field(default=None, description='表类型')
    table_comment: Optional[str] = Field(default=None, description='表描述')


class GenTableBaseSchema(BaseModel):
    """代码生成业务表基础模型（创建/更新共享字段）。
    - 说明：`params`为前端结构体，后端持久化为`options`的JSON。
    """
    model_config = ConfigDict(from_attributes=True)

    table_name: str= Field(..., description='表名称')
    table_comment: Optional[str] = Field(default=None, description='表描述')
    sub_table_name: Optional[str] = Field(default=None, description='关联子表的表名')
    sub_table_fk_name: Optional[str] = Field(default=None, description='子表关联的外键名')
    class_name: Optional[str] = Field(default=None, description='实体类名称')
    package_name: Optional[str] = Field(default=None, description='生成包路径')
    module_name: Optional[str] = Field(default=None, description='生成模块名')
    business_name: Optional[str] = Field(default=None, description='生成业务名')
    function_name: Optional[str] = Field(default=None, description='生成功能名')
    gen_type: Optional[Literal['0', '1']] = Field(default=None, description='生成代码方式（0zip压缩包 1生成项目路径）')
    options: Optional[str] = Field(default=None, description='其它生成选项（JSON字符串）')
    description: Optional[str] = Field(default=None, description='功能描述')


class GenTableSchema(GenTableBaseSchema):
    """代码生成业务表更新模型（扩展聚合字段）。
    - 聚合：`columns`字段包含字段列表；`pk_column`主键字段；子表结构`sub_table`。
    """

    pk_column: Optional['GenTableColumnOutSchema'] = Field(default=None, description='主键信息')
    sub_table: Optional['GenTableSchema'] = Field(default=None, description='子表信息')
    columns: Optional[List['GenTableColumnOutSchema']] = Field(default=None, description='表列信息')
    parent_menu_id: Optional[int] = Field(default=None, description='上级菜单ID字段')
    parent_menu_name: Optional[str] = Field(default=None, description='上级菜单名称字段')
    sub: Optional[bool] = Field(default=None, description='是否为子表')


class GenTableOutSchema(GenTableSchema, BaseSchema):
    """业务表输出模型（面向控制器/前端）。
    - 清洗：统一处理None值，保证`columns`为列表；文本字段为空字符串。
    - 兼容：既支持传入ORM对象，也支持字典输入。
    """
    model_config = ConfigDict(from_attributes=True)


class GenTableColumnSchema(BaseModel):
    """代码生成业务表字段创建模型（原始字段+生成配置）。
    - 原始：`column_name/column_type/column_comment` 等。
    - 生成：`python_type/html_type/query_type/dict_type` 等由工具初始化。
    - 标记：所有 is_* 字段默认使用字符串'1'表示启用，便于前端和模板处理。
    """
    model_config = ConfigDict(from_attributes=True)

    table_id: Optional[int] = Field(default=None, description='归属表编号')
    column_name: Optional[str] = Field(default=None, description='列名称')
    column_comment: Optional[str] = Field(default=None, description='列描述')
    column_type: Optional[str] = Field(default=None, description='列类型')
    python_type: Optional[str] = Field(default=None, description='python类型')
    python_field: Optional[str] = Field(default=None, description='python字段名')
    is_pk: Optional[str] = Field(default=None, description='是否主键（1是）')
    is_increment: Optional[str] = Field(default=None, description='是否自增（1是）')
    is_required: Optional[str] = Field(default=None, description='是否必填（1是）')
    is_unique: Optional[str] = Field(default=None, description='是否唯一（1是）')
    is_insert: Optional[str] = Field(default=None, description='是否为插入字段（1是）')
    is_edit: Optional[str] = Field(default=None, description='是否编辑字段（1是）')
    is_list: Optional[str] = Field(default=None, description='是否列表字段（1是）')
    is_query: Optional[str] = Field(default=None, description='是否查询字段（1是）')
    query_type: Optional[str] = Field(default=None, description='查询方式（等于、不等于、大于、小于、范围）')
    html_type: Optional[str] = Field(default=None, description='显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）')
    dict_type: Optional[str] = Field(default=None, description='字典类型')
    sort: Optional[int] = Field(default=None, description='排序')
    description: Optional[str] = Field(default=None, description='功能描述')


class GenTableColumnOutSchema(GenTableColumnSchema, BaseSchema):
    """业务表字段输出模型（布尔派生+便捷字段）。
    - 布尔：将字符串 is_* 转为布尔 `pk/increment/...`，供前端/模板快捷使用。
    - 便捷：`cap_python_field` 存放大驼峰字段名（模板场景常用）。
    """
    model_config = ConfigDict(from_attributes=True)

    cap_python_field: Optional[str] = Field(default=None, description='字段大写形式')
    pk: Optional[bool] = Field(default=False, description='是否主键')
    increment: Optional[bool] = Field(default=False, description='是否自增')
    required: Optional[bool] = Field(default=False, description='是否必填')
    unique: Optional[bool] = Field(default=False, description='是否唯一')
    insert: Optional[bool] = Field(default=False, description='是否为插入字段')
    edit: Optional[bool] = Field(default=False, description='是否编辑字段')
    list: Optional[bool] = Field(default=False, description='是否列表字段')
    query: Optional[bool] = Field(default=False, description='是否查询字段')
    super_column: Optional[bool] = Field(default=False, description='是否为基类字段')
    usable_column: Optional[bool] = Field(default=False, description='是否为基类字段白名单')
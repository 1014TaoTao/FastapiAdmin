# -*- coding: utf-8 -*-

import re
from typing import List

from app.common.constant import GenConstant
from app.config.setting import settings
from app.utils.string_util import StringUtil
from app.api.v1.module_generator.gencode.schema import GenTableOutSchema, GenTableSchema, GenTableColumnSchema


class GenUtils:
    """代码生成器工具类"""

    @classmethod
    def init_table(cls, gen_table: GenTableSchema) -> None:
        """
        初始化表信息

        参数:
        - gen_table (GenTableSchema): 业务表对象。

        返回:
        - None
        """
        # 只有当字段为None时才设置默认值
        gen_table.class_name = cls.convert_class_name(gen_table.table_name or "")
        gen_table.package_name = settings.package_name
        gen_table.module_name = settings.package_name.split('.')[-1]
        gen_table.business_name = gen_table.table_name.split('_')[-1]
        gen_table.function_name = re.sub(r'(?:表|测试)', '', gen_table.table_comment or "")

    @classmethod
    def init_column_field(cls, column: GenTableColumnSchema, table: GenTableOutSchema) -> None:
        """
        初始化列属性字段

        参数:
        - column (GenTableColumnSchema): 业务表字段对象。
        - table (GenTableOutSchema): 业务表对象。

        返回:
        - None
        """
        data_type = cls.get_db_type(column.column_type or "")
        column_name = column.column_name or ""
        column.table_id = table.id
        column.python_field = cls.to_camel_case(column_name)
        # 只有当python_type为None时才设置默认类型
        column.python_type = StringUtil.get_mapping_value_by_key_ignore_case(GenConstant.DB_TO_PYTHON, data_type)
        # 查询类型：优先根据字段语义（如以name结尾走LIKE），否则默认EQ
        column.query_type = GenConstant.QUERY_LIKE

        # 确保is_pk等字段为字符串格式
        # 将布尔值或其他类型转换为字符串'1'或'0'
        if column.is_pk is not None and not isinstance(column.is_pk, str):
            column.is_pk = '1' if bool(column.is_pk) else '0'
        if column.is_increment is not None and not isinstance(column.is_increment, str):
            column.is_increment = '1' if bool(column.is_increment) else '0'
        if column.is_required is not None and not isinstance(column.is_required, str):
            column.is_required = '1' if bool(column.is_required) else '0'
        
        # 确保None值默认为'0'
        column.is_pk = column.is_pk or '0'
        column.is_increment = column.is_increment or '0'
        column.is_required = column.is_required or '0'

        if column.html_type is None:
            if cls.arrays_contains(GenConstant.COLUMNTYPE_STR, data_type) or cls.arrays_contains(
                GenConstant.COLUMNTYPE_TEXT, data_type
            ):
                # 字符串长度超过500设置为文本域
                column_length = cls.get_column_length(column.column_type or "")
                html_type = (
                    GenConstant.HTML_TEXTAREA
                    if column_length >= 500 or cls.arrays_contains(GenConstant.COLUMNTYPE_TEXT, data_type)
                    else GenConstant.HTML_INPUT
                )
                column.html_type = html_type
            elif cls.arrays_contains(GenConstant.COLUMNTYPE_TIME, data_type):
                column.html_type = GenConstant.HTML_DATETIME
            elif cls.arrays_contains(GenConstant.COLUMNTYPE_NUMBER, data_type):
                column.html_type = GenConstant.HTML_INPUT
            elif column_name.lower().endswith("status"):
                column.html_type = GenConstant.HTML_RADIO
            elif column_name.lower().endswith("type") or column_name.lower().endswith("sex"):
                column.html_type = GenConstant.HTML_SELECT
            elif column_name.lower().endswith("image"):
                column.html_type = GenConstant.HTML_IMAGE_UPLOAD
            elif column_name.lower().endswith("file"):
                column.html_type = GenConstant.HTML_FILE_UPLOAD
            elif column_name.lower().endswith("content"):
                column.html_type = GenConstant.HTML_EDITOR
            else:
                column.html_type = GenConstant.HTML_INPUT

        # 只有当is_insert为None时才设置插入字段（默认所有字段都需要插入）
        if column.is_insert is None:
            column.is_insert = GenConstant.REQUIRE
        else:
            # 确保is_insert为字符串格式
            column.is_insert = str(column.is_insert) if column.is_insert is not None else '0'
            
        # 只有当is_edit为None时才设置编辑字段
        if column.is_edit is None:
            if not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_EDIT, column_name) and column.is_pk != '1':
                column.is_edit = GenConstant.REQUIRE
            else:
                column.is_edit = '0'
        else:
            # 确保is_edit为字符串格式
            column.is_edit = str(column.is_edit) if column.is_edit is not None else '0'
            
        # 只有当is_list为None时才设置列表字段
        if column.is_list is None:
            if not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_LIST, column_name) and column.is_pk != '1':
                column.is_list = GenConstant.REQUIRE
            else:
                column.is_list = '0'
        else:
            # 确保is_list为字符串格式
            column.is_list = str(column.is_list) if column.is_list is not None else '0'
            
        # 只有当is_query为None时才设置查询字段
        if column.is_query is None:
            if not cls.arrays_contains(GenConstant.COLUMNNAME_NOT_QUERY, column_name) and column.is_pk != '1':
                column.is_query = GenConstant.REQUIRE
            else:
                column.is_query = '0'
        else:
            # 确保is_query为字符串格式
            column.is_query = str(column.is_query) if column.is_query is not None else '0'

    @classmethod
    def arrays_contains(cls, arr: List[str], target_value: str) -> bool:
        """
        校验数组是否包含指定值

        param arr: 数组
        param target_value: 需要校验的值
        :return: 校验结果
        """
        return target_value in arr

    @classmethod
    def convert_class_name(cls, table_name: str) -> str:
        """
        表名转换成 Python 类名

        参数:
        - table_name (str): 业务表名。

        返回:
        - str: Python 类名。
        """
        auto_remove_pre = settings.auto_remove_pre
        table_prefix = settings.table_prefix
        if auto_remove_pre and table_prefix:
            search_list = table_prefix.split(',')
            table_name = cls.replace_first(table_name, search_list)
        return StringUtil.convert_to_camel_case(table_name)

    @classmethod
    def replace_first(cls, input_string: str, search_list: List[str]) -> str:
        """
        批量替换前缀

        参数:
        - input_string (str): 需要被替换的字符串。
        - search_list (List[str]): 可替换的字符串列表。

        返回:
        - str: 替换后的字符串。
        """
        for search_string in search_list:
            if input_string.startswith(search_string):
                return input_string.replace(search_string, '', 1)
        return input_string

    @classmethod
    def get_db_type(cls, column_type: str) -> str:
        """
        获取数据库类型字段

        参数:
        - column_type (str): 字段类型。

        返回:
        - str: 数据库类型。
        """
        if '(' in column_type:
            return column_type.split('(')[0]
        return column_type

    @classmethod
    def get_column_length(cls, column_type: str) -> int:
        """
        获取字段长度

        参数:
        - column_type (str): 字段类型，例如 'varchar(255)' 或 'decimal(10,2)'

        返回:
        - int: 字段长度（优先取第一个长度值，无法解析时返回0）。
        """
        if '(' in column_type:
            length = len(column_type.split('(')[1].split(')')[0])
            return length
        return 0

    @classmethod
    def split_column_type(cls, column_type: str) -> List[str]:
        """
        拆分列类型

        参数:
        - column_type (str): 字段类型。

        返回:
        - List[str]: 拆分结果。
        """
        if '(' in column_type and ')' in column_type:
            return column_type.split('(')[1].split(')')[0].split(',')
        return []
    
    @classmethod
    def to_camel_case(cls, text: str) -> str:
        """
        将字符串转换为驼峰命名

        param text: 需要转换的字符串
        :return: 驼峰命名
        """
        parts = text.split('_')
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])
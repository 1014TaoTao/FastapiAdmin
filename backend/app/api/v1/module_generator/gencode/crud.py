# -*- coding:utf-8 -*-

from sqlalchemy.engine.row import Row
from sqlalchemy import and_, select, text
from typing import List, Optional, Sequence, Dict, Union, Any

from app.core.logger import logger
from app.config.setting import settings
from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .param import GenTableQueryParam, GenTableColumnQueryParam
from .model import GenTableModel, GenTableColumnModel
from .schema import (
    GenTableSchema,
    GenTableOutSchema,
    GenTableColumnSchema,
    GenTableColumnOutSchema,
    GenDBTableSchema,
)


class GenTableCRUD(CRUDBase[GenTableModel, GenTableSchema, GenTableSchema]):
    """代码生成业务表模块数据库操作层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化CRUD操作层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        super().__init__(model=GenTableModel, auth=auth)

    async def get_gen_table_by_id(self, table_id: int, preload: Optional[List[Union[str, Any]]] = None) -> Optional[GenTableModel]:
        """
        根据业务表ID获取需要生成的业务表信息。

        参数:
        - table_id (int): 业务表ID。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - GenTableModel | None: 业务表信息对象。
        """
        return await self.get(id=table_id, preload=preload)

    async def get_gen_table_by_name(self, table_name: str, preload: Optional[List[Union[str, Any]]] = None) -> Optional[GenTableModel]:
        """
        根据业务表名称获取需要生成的业务表信息。

        参数:
        - table_name (str): 业务表名称。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - GenTableModel | None: 业务表信息对象。
        """
        return await self.get(table_name=table_name, preload=preload)

    async def get_gen_table_all(self, preload: Optional[List[Union[str, Any]]] = None) -> Sequence[GenTableModel]:
        """
        获取所有业务表信息。

        参数:
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableModel]: 所有业务表信息列表。
        """
        return await self.list(preload=preload)

    async def get_gen_table_list(self, search: Optional[GenTableQueryParam] = None, preload: Optional[List[Union[str, Any]]] = None) -> Sequence[GenTableModel]:
        """
        根据查询参数获取代码生成业务表列表信息。

        参数:
        - search (GenTableQueryParam | None): 查询参数对象。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableModel]: 业务表列表信息。
        """
        # 使用基础CRUD的list与like检索
        return await self.list(search=search.__dict__, order_by=[{"created_at": "desc"}], preload=preload)

    async def add_gen_table(self, add_model: GenTableSchema) -> GenTableModel:
        """
        新增业务表信息。

        参数:
        - add_model (GenTableSchema): 新增业务表信息模型。

        返回:
        - GenTableModel: 新增的业务表信息对象。
        """
        return await self.create(add_model.model_dump(exclude_unset=True, exclude={"sub", "tree", "crud"}))

    async def edit_gen_table(self, table_id: int, edit_model: GenTableSchema) -> GenTableSchema:
        """
        修改业务表信息。

        参数:
        - table_id (int): 业务表ID。
        - edit_model (GenTableSchema): 修改业务表信息模型。

        返回:
        - GenTableSchema: 修改后的业务表信息模型。
        """
        # 排除嵌套对象字段，避免SQLAlchemy尝试直接将字典设置到模型实例上
        data_dict = edit_model.model_dump(exclude_unset=True, exclude={"columns", "pk_column", "sub_table", "sub"})
        obj = await self.update(id=table_id, data=data_dict)
        return GenTableSchema.model_validate(obj)

    async def delete_gen_table(self, ids: List[int]) -> None:
        """
        删除业务表信息。除了系统表。

        参数:
        - ids (List[int]): 业务表ID列表。
        """
        await self.delete(ids=ids)

    async def get_db_table_list(self, search: Optional[GenTableQueryParam] = None) -> list[Dict]:
        """
        根据查询参数获取数据库表列表信息。

        参数:
        - search (GenTableQueryParam | None): 查询参数对象。

        返回:
        - list[Dict]: 数据库表列表信息（已转为可序列化字典）。
        """

        # 使用更健壮的方式检测数据库方言
        if settings.DATABASE_TYPE == "postgresql":
            # 修复：PostgreSQL不提供table_comment，使用pg_catalog获取注释
            query_sql = (
                select(
                    text("t.table_catalog as database_name"),
                    text("t.table_name as table_name"),
                    text("t.table_type as table_type"),
                    text("pd.description as table_comment"),
                )
                .select_from(text(
                    "information_schema.tables t \n"
                    "LEFT JOIN pg_catalog.pg_class c ON c.relname = t.table_name \n"
                    "LEFT JOIN pg_catalog.pg_namespace n ON n.nspname = t.table_schema AND c.relnamespace = n.oid \n"
                    "LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = c.oid AND pd.objsubid = 0"
                ))
                .where(
                    and_(
                        text("t.table_catalog = (select current_database())"),
                        text("t.is_insertable_into = 'YES'"),
                        text("t.table_schema = 'public'"),
                    )
                )
            )
        elif settings.DATABASE_TYPE == "mysql":
            query_sql = (
                select(
                    text("table_schema as database_name"),
                    text("table_name as table_name"),
                    text("table_type as table_type"),
                    text("table_comment as table_comment"),
                )
                .select_from(text("information_schema.tables"))
                .where(
                    and_(
                        text("table_schema = (select database())"),
                    )
                )
            )
        else:
            query_sql = (
                select(
                    text("'fastapiadmin' as database_name"),  # SQLite没有数据库名概念，设为空字符串
                    text("name as table_name"),
                    text("type as table_type"),
                    text("name as table_comment"),  # SQLite中使用name作为表名和注释
                )
                .select_from(text("sqlite_master"))
                .where(
                    and_(
                        text("type = 'table'"),
                    )   
                )
            )
        
        # 动态条件构造
        params = {}
        if search and search.table_name:
            if settings.DATABASE_TYPE == "sqlite":
                query_sql = query_sql.where(
                    text("lower(name) like lower(:table_name)")
                )
            else:
                query_sql = query_sql.where(
                    text("lower(table_name) like lower(:table_name)")
                )
            params['table_name'] = f"%{search.table_name}%"
        if search and search.table_comment:
            if settings.DATABASE_TYPE == "sqlite":
                query_sql = query_sql.where(
                    text("lower(name) like lower(:table_comment)")
                )
            else:
                query_sql = query_sql.where(
                    text("lower(table_comment) like lower(:table_comment)")
                )
            params['table_comment'] = f"%{search.table_comment}%"

        # 执行查询并绑定参数
        all_data = (await self.db.execute(query_sql, params)).fetchall()

        # 将Row对象转换为字典列表，解决JSON序列化问题
        dict_data = []
        for row in all_data:
            # 检查row是否为Row对象
            if isinstance(row, Row):
                # 使用._mapping获取字典
                dict_row = GenDBTableSchema(**dict(row._mapping)).model_dump()
                dict_data.append(dict_row)
            else:
                dict_row = GenDBTableSchema(**dict(row)).model_dump()
                dict_data.append(dict_row)
        return dict_data

    async def get_db_table_list_by_names(self, table_names: List[str]) -> list[GenDBTableSchema]:
        """
        根据业务表名称列表获取数据库表信息。

        参数:
        - table_names (List[str]): 业务表名称列表。

        返回:
        - list[GenDBTableSchema]: 数据库表信息对象列表。
        """
        # 使用更健壮的方式检测数据库方言
        if settings.DATABASE_TYPE == "postgresql":
            # 修复：PostgreSQL不提供table_comment，使用pg_catalog获取注释
            query_sql = (
                select(
                    text("t.table_catalog as database_name"),
                    text("t.table_name as table_name"),
                    text("t.table_type as table_type"),
                    text("pd.description as table_comment"),
                )
                .select_from(text(
                    "information_schema.tables t \n"
                    "LEFT JOIN pg_catalog.pg_class c ON c.relname = t.table_name \n"
                    "LEFT JOIN pg_catalog.pg_namespace n ON n.nspname = t.table_schema AND c.relnamespace = n.oid \n"
                    "LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = c.oid AND pd.objsubid = 0"
                ))
                .where(
                    and_(
                        text("t.table_catalog = (select current_database())"),
                        text("t.is_insertable_into = 'YES'"),
                        text("t.table_schema = 'public'"),
                    )
                )
            )
        elif settings.DATABASE_TYPE == "mysql":
            query_sql = (
                select(
                    text("table_schema as database_name"),
                    text("table_name as table_name"),
                    text("table_type as table_type"),
                    text("table_comment as table_comment"),
                )
                .select_from(text("information_schema.tables"))
                .where(
                    and_(
                        text("table_schema = (select database())"),
                    )
                )
            )
        else:
            query_sql = (
                select(
                    text("'fastapiadmin' as database_name"),  # SQLite没有数据库名概念，设为空字符串
                    text("name as table_name"),
                    text("type as table_type"),
                    text("name as table_comment"),  # SQLite中使用name作为表名和注释
                )
                .select_from(text("sqlite_master"))
                .where(
                    and_(
                        text("type = 'table'"),
                    )   
                )
            )
        
        table_names_str = "','".join(table_names)
        # 修复SQL查询中的参数绑定问题
        if table_names:
            if settings.DATABASE_TYPE == "sqlite":
                # 对于SQLite，我们直接在SQL中使用表名，因为参数绑定有问题
                query_sql = query_sql.where(
                    text(f"name IN ('{table_names_str}')")
                )
                gen_db_table_list = (await self.db.execute(query_sql)).fetchall()
            else:
                # MySQL和PostgreSQL使用IN拼接（注意已在上方限定schema范围）
                query_sql = query_sql.where(
                    text(f"table_name IN ('{table_names_str}')")
                )
                gen_db_table_list = (await self.db.execute(query_sql)).fetchall()
        else:
            gen_db_table_list = (await self.db.execute(query_sql)).fetchall()
        
        # 将Row对象转换为字典列表，解决JSON序列化问题
        dict_data = []
        for row in gen_db_table_list:
            # 检查row是否为Row对象
            if isinstance(row, Row):
                # 使用._mapping获取字典
                dict_row = GenDBTableSchema(**dict(row._mapping))
                dict_data.append(dict_row)
            else:
                dict_row = GenDBTableSchema(**dict(row))
                dict_data.append(dict_row)
        return dict_data

    async def create_table_by_sql(self, sql: str) -> bool:
        """
        根据SQL语句创建表结构。

        参数:
        - sql (str): 创建表的SQL语句。

        返回:
        - bool: 是否创建成功。
        """
        try:
            await self.db.execute(text(sql))
            # 提交事务
            await self.db.commit()
            await self.db.flush()
            return True
        except Exception as e:
            # 如果发生异常，回滚事务
            await self.db.rollback()
            logger.error(f"创建表时发生错误: {e}")
            return False


class GenTableColumnCRUD(CRUDBase[GenTableColumnModel, GenTableColumnSchema, GenTableColumnSchema]):
    """代码生成业务表字段模块数据库操作层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化CRUD操作层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        super().__init__(model=GenTableColumnModel, auth=auth)

    async def get_gen_table_column_by_id(self, id: int, preload: Optional[List[Union[str, Any]]] = None) -> Optional[GenTableColumnModel]:
        """根据业务表字段ID获取业务表字段信息。

        参数:
        - id (int): 业务表字段ID。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Optional[GenTableColumnModel]: 业务表字段信息对象。
        """
        return await self.get(id=id, preload=preload)
    
    async def get_gen_table_column_list_by_table_id(self, table_id: int, preload: Optional[List[Union[str, Any]]] = None) -> Optional[GenTableColumnModel]:
        """根据业务表ID获取业务表字段列表信息。

        参数:
        - table_id (int): 业务表ID。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Optional[GenTableColumnModel]: 业务表字段列表信息对象。
        """
        return await self.get(table_id=table_id, preload=preload)
    
    async def list_gen_table_column_crud_by_table_id(self, table_id: int, order_by: Optional[List[Dict[str, str]]] = None, preload: Optional[List[Union[str, Any]]] = None) -> Sequence[GenTableColumnModel]:
        """根据业务表ID查询业务表字段列表。

        参数:
        - table_id (int): 业务表ID。
        - order_by (Optional[List[Dict[str, str]]]): 排序字段列表，每个元素为{"field": "字段名", "order": "asc" | "desc"}。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableColumnModel]: 业务表字段列表信息对象序列。
        """
        return await self.list(search={"table_id": table_id}, order_by=order_by, preload=preload)

    async def get_gen_db_table_columns_by_name(self, table_name: str | None) -> List[GenTableColumnOutSchema]:
        """
        根据业务表名称获取业务表字段列表信息。

        参数:
        - table_name (str | None): 业务表名称。

        返回:
        - List[GenTableColumnOutSchema]: 业务表字段列表信息对象。
        """
        # 检查表名是否为空
        if not table_name:
            raise ValueError("数据表名称不能为空")

        # 兼容SQLite和MySQL/PostgreSQL
        if settings.DATABASE_TYPE == "postgresql":
            # 修复：PostgreSQL的主键/自增/注释需要关联系统表
            query_sql = """
                SELECT
                    c.column_name,
                    (CASE WHEN (c.is_nullable = 'NO' AND (tc.constraint_type IS DISTINCT FROM 'PRIMARY KEY')) THEN '1' ELSE '0' END) AS is_required,
                    (CASE WHEN (tc.constraint_type = 'PRIMARY KEY') THEN '1' ELSE '0' END) AS is_pk,
                    c.ordinal_position AS sort,
                    COALESCE(pgd.description, '') AS column_comment,
                    (CASE WHEN c.column_default LIKE 'nextval%' THEN '1' ELSE '0' END) AS is_increment,
                    c.udt_name AS column_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.key_column_usage kcu
                  ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name AND kcu.table_schema = c.table_schema
                LEFT JOIN information_schema.table_constraints tc
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_name = c.table_name AND tc.table_schema = c.table_schema
                LEFT JOIN pg_catalog.pg_statio_all_tables st
                  ON st.relname = c.table_name
                LEFT JOIN pg_catalog.pg_description pgd
                  ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                WHERE c.table_catalog = current_database()
                  AND c.table_schema = 'public'
                  AND c.table_name = :table_name
                ORDER BY c.ordinal_position
            """
        elif settings.DATABASE_TYPE == "mysql":
            query_sql = """
                SELECT
                    column_name,
                    (CASE WHEN (is_nullable = 'no' AND column_key != 'PRI') THEN '1' ELSE '0' END) AS is_required,
                    (CASE WHEN column_key = 'PRI' THEN '1' ELSE '0' END) AS is_pk,
                    ordinal_position AS sort,
                    column_comment,
                    (CASE WHEN extra = 'auto_increment' THEN '1' ELSE '0' end) AS is_increment,
                    column_type
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = (SELECT DATABASE())
                    AND table_name = :table_name
                ORDER BY ordinal_position
            """
        else:
            # 修复SQLite查询语句，使用PRAGMA获取表结构信息
            query_sql = """
                SELECT
                    name as column_name,
                    (CASE WHEN (type != '' AND pk != 1) THEN '1' ELSE '0' END) AS is_required,
                    (CASE WHEN pk = 1 THEN '1' ELSE '0' END) AS is_pk,
                    cid AS sort,
                    '' as column_comment,
                    (CASE WHEN type LIKE '%AUTOINCREMENT%' THEN '1' ELSE '0' END) AS is_increment,
                    type as column_type
                FROM 
                    pragma_table_info(:table_name)
                ORDER BY cid
            """
        
        query = text(query_sql).bindparams(table_name=table_name)
        rows = (await self.db.execute(query)).fetchall()
        result = [
            GenTableColumnOutSchema(
                column_name=row[0],
                is_required=row[1],
                is_pk=row[2],
                sort=row[3],
                column_comment=row[4],
                is_increment=row[5],
                column_type=row[6]
            )
            for row in rows
        ]
        
        return result

    async def list_gen_table_column_crud(self, search: Optional[Dict] = None, order_by: Optional[List[Dict[str, str]]] = None, preload: Optional[List[Union[str, Any]]] = None) -> Sequence[GenTableColumnModel]:
        """根据业务表字段查询业务表字段列表。

        参数:
        - search (Optional[Dict]): 查询参数，例如{"table_id": 1}。
        - order_by (Optional[List[Dict[str, str]]]): 排序字段列表，每个元素为{"field": "字段名", "order": "asc" | "desc"}。
        - preload (Optional[List[Union[str, Any]]]): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[GenTableColumnModel]: 业务表字段列表信息对象序列。
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_gen_table_column_crud(self, data: GenTableColumnSchema) -> Optional[GenTableColumnModel]:
        """创建业务表字段。

        参数:
        - data (GenTableColumnSchema): 业务表字段模型。

        返回:
        - Optional[GenTableColumnModel]: 业务表字段列表信息对象。
        """
        return await self.create(data=data)

    async def update_gen_table_column_crud(self, id: int, data: GenTableColumnSchema) -> Optional[GenTableColumnModel]:
        """更新业务表字段。

        参数:
        - id (int): 业务表字段ID。
        - data (GenTableColumnSchema): 业务表字段模型。

        返回:
        - Optional[GenTableColumnModel]: 业务表字段列表信息对象。
        """
        # 将对象转换为字典，避免SQLAlchemy直接操作对象时出现的状态问题
        data_dict = data.model_dump(exclude_unset=True)
        return await self.update(id=id, data=data_dict)

    async def delete_gen_table_column_by_table_id_dao(self, table_ids: List[int]) -> None:
        """根据业务表ID批量删除业务表字段。

        参数:
        - table_ids (List[int]): 业务表ID列表。

        返回:
        - None
        """
        # 先查询出这些表ID对应的所有字段ID
        query = select(GenTableColumnModel.id).where(GenTableColumnModel.table_id.in_(table_ids))
        result = await self.db.execute(query)
        column_ids = [row[0] for row in result.fetchall()]
        
        # 如果有字段ID，则删除这些字段
        if column_ids:
            await self.delete(ids=column_ids)

    async def delete_gen_table_column_by_column_id_dao(self, column_ids: List[int]) -> None:
        """根据业务表字段ID批量删除业务表字段。

        参数:
        - column_ids (List[int]): 业务表字段ID列表。

        返回:
        - None
        """
        return await self.delete(ids=column_ids)
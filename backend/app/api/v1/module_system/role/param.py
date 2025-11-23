# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import Query

from app.core.validator import DateTimeStr


class RoleQueryParam:
    """角色管理查询参数"""

    def __init__(
        self,
        name: Optional[str] = Query(None, description="角色名称"),
        status: Optional[bool] = Query(None, description="是否可用"),
        creator: Optional[int] = Query(None, description="创建人"),
        start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
        end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
    ) -> None:
        
        # 模糊查询字段
        self.name = ("like", name)

        # 精确查询字段
        self.created_id = creator
        self.status = status
        
        # 时间范围查询
        if start_time and end_time:
            self.created_at = ("between", (start_time, end_time))

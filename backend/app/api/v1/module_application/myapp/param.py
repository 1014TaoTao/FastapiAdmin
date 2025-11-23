# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import Query

from app.core.validator import DateTimeStr

class ApplicationQueryParam:
    """应用系统查询参数"""

    def __init__(
        self,
        name: Optional[str] = Query(None, description="应用名称"),
        status: Optional[bool] = Query(None, description="是否启用"),
        creator: Optional[int] = Query(None, description="创建人"),
        start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
        end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
    ) -> None:
        
        # 模糊查询字段
        self.name = ("like", name) if name else None

        # 精确查询字段
        self.status = status
        self.created_id = creator

        # 时间范围查询
        if start_time and end_time:
            self.created_at = ("between", (start_time, end_time))



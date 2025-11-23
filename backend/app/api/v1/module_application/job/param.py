# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import Query

from app.core.validator import DateTimeStr


class JobQueryParam:
    """定时任务查询参数"""

    def __init__(
        self,
        name: Optional[str] = Query(None, description="任务名称"),
        status: Optional[bool] = Query(None, description="状态: 启动,停止"),
        creator: Optional[int] = Query(None, description="创建人"),
        start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
        end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
    ) -> None:
        
        # 模糊查询字段
        self.name = ("like", f"%{name}%") if name else None
        
        # 精确查询字段
        self.created_id = creator
        self.status = status
        
        # 时间范围查询
        if start_time and end_time:
            self.created_at = ("between", (start_time, end_time))


class JobLogQueryParam:
    """定时任务查询参数"""

    def __init__(
            self,
            job_id: Optional[int] = Query(None, description="定时任务ID"),
            job_name: Optional[str] = Query(None, description="任务名称"),
            status: Optional[bool] = Query(None, description="状态: 正常,失败"),
            start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
            end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
    ) -> None:
        # 定时任务ID查询
        self.job_id = job_id
        # 模糊查询字段
        self.job_name = ("like", job_name)
        # 精确查询字段
        self.status = status
        # 时间范围查询
        if start_time and end_time:
            self.create_time = ("between", (start_time, end_time))
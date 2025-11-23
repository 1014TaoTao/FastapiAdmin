# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import Query

from app.core.validator import DateTimeStr


class NoticeQueryParam:
    """公告通知查询参数"""

    def __init__(
        self,
        notice_title: Optional[str] = Query(None, description="公告标题"),
        notice_type: Optional[str] = Query(None, description="公告类型"),
        status: Optional[bool] = Query(None, description="是否可用"),
        creator: Optional[int] = Query(None, description="创建人"),
        start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
        end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
    ) -> None:
        
        # 模糊查询字段
        self.notice_title = ("like", notice_title)

        # 精确查询字段
        self.created_id = creator
        self.status = status
        self.notice_type = notice_type

        # 时间范围查询
        if start_time and end_time:
            self.created_at = ("between", (start_time, end_time))



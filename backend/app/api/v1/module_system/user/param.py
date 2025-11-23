# -*- coding: utf-8 -*-

from typing import Optional
from fastapi import Query

from app.core.validator import DateTimeStr


class UserQueryParam:
    """用户管理查询参数"""

    def __init__(
        self,
        username: Optional[str] = Query(None, description="用户名"),
        name: Optional[str] = Query(None, description="名称"),
        mobile: Optional[str] = Query(None, description="手机号", pattern=r'^1[3-9]\d{9}$'),
        email: Optional[str] = Query(None, description="邮箱", pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'), 
        dept_id: Optional[int] = Query(None, description="部门ID"),
        status: Optional[bool] = Query(None, description="是否可用"),
        start_time: Optional[DateTimeStr] = Query(None, description="开始时间", example="2025-01-01 00:00:00"),
        end_time: Optional[DateTimeStr] = Query(None, description="结束时间", example="2025-12-31 23:59:59"),
        creator: Optional[int] = Query(None, description="创建人"),
    ) -> None:
        
        # 模糊查询字段
        self.username = ("like", username)
        self.name = ("like", name)
        self.mobile = ("like", mobile)
        self.email = ("like", email)

        # 精确查询字段
        self.dept_id = dept_id
        self.created_id = creator
        self.status = status
        
        # 时间范围查询
        if start_time and end_time:
            self.created_at = ("between", (start_time, end_time))

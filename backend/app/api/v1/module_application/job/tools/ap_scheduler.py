# -*- coding: utf-8 -*-

import asyncio
import json
import importlib
from datetime import datetime
from typing import Any
from asyncio import iscoroutinefunction
from apscheduler.job import Job
from apscheduler.events import JobExecutionEvent, EVENT_ALL, JobEvent
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore 
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from concurrent.futures import ThreadPoolExecutor

from app.config.setting import settings
from app.core.database import engine, db_session, async_db_session
from app.core.exceptions import CustomException
from app.core.logger import log
from app.utils.cron_util import CronUtil

from app.api.v1.module_application.job.model import JobModel

job_stores = {
    'default': MemoryJobStore(),
    'sqlalchemy': SQLAlchemyJobStore(url=settings.DB_URI, engine=engine), 
    'redis': RedisJobStore(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        username=settings.REDIS_USER,
        password=settings.REDIS_PASSWORD,
        db=int(settings.REDIS_DB_NAME),
    ),
}
# 配置执行器
executors = {
    'default': AsyncIOExecutor(), 
    'processpool': ProcessPoolExecutor(max_workers=1)  # 减少进程数量以减少资源消耗
}
# 配置默认参数
job_defaults = {
    'coalesce': True,  # 合并执行错过的任务
    'max_instances': 1,  # 最大实例数
}
# 配置调度器
scheduler = AsyncIOScheduler()
scheduler.configure(
    jobstores=job_stores, 
    executors=executors, 
    job_defaults=job_defaults,
    timezone='Asia/Shanghai'
)

class SchedulerUtil:
    """
    定时任务相关方法
    """
    @classmethod
    def scheduler_event_listener(cls, event: JobEvent | JobExecutionEvent) -> None:
        """
        监听任务执行事件。
    
        参数:
        - event (JobEvent | JobExecutionEvent): 任务事件对象。
    
        返回:
        - None
        """
        # 只处理任务执行相关事件，不处理任务添加、删除等事件
        if not isinstance(event, JobExecutionEvent):
            return
            
        # 延迟导入避免循环导入
        from app.api.v1.module_application.job.model import JobLogModel
        
        # 获取事件类型和任务ID
        event_type = event.__class__.__name__
        # 初始化任务状态
        status = True
        exception_info = ''
        if isinstance(event, JobExecutionEvent) and event.exception:
            exception_info = str(event.exception)
            status = False
        if hasattr(event, 'job_id'):
            job_id = event.job_id
            query_job = cls.get_job(job_id=job_id)
            if query_job:
                query_job_info = query_job.__getstate__()
                # 获取任务名称
                job_name = query_job_info.get('name')
                # 获取任务组名
                job_group = query_job._jobstore_alias
                # # 获取任务执行器
                job_executor = query_job_info.get('executor')
                # 获取调用目标字符串
                invoke_target = query_job_info.get('func')
                # 获取调用函数位置参数
                job_args = ','.join(map(str, query_job_info.get('args', [])))
                # 获取调用函数关键字参数
                job_kwargs = json.dumps(query_job_info.get('kwargs'))
                # 获取任务触发器
                job_trigger = str(query_job_info.get('trigger'))
                # 构造日志消息
                job_message = f"事件类型: {event_type}, 任务ID: {job_id}, 任务名称: {job_name}, 状态: {status}, 任务组: {job_group}, 错误详情: {exception_info}, 执行于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # 创建ORM对象
                job_log = JobLogModel(
                    job_name=job_name,
                    job_group=job_group,
                    job_executor=job_executor,
                    invoke_target=invoke_target,
                    job_args=job_args,
                    job_kwargs=job_kwargs,
                    job_trigger=job_trigger,
                    job_message=job_message,
                    status=status,
                    exception_info=exception_info,
                    created_time=datetime.now(),
                    updated_time=datetime.now(),
                    job_id=job_id,
                )
                
                # 使用线程池执行操作以避免阻塞调度器和数据库锁定问题
                executor = ThreadPoolExecutor(max_workers=1)
                executor.submit(cls._save_job_log_async_wrapper, job_log)
                executor.shutdown(wait=False)

    @classmethod
    def _save_job_log_async_wrapper(cls, job_log) -> None:
        """
        异步保存任务日志的包装器函数，在独立线程中运行
        
        参数:
        - job_log (JobLogModel): 任务日志对象
        
        返回:
        - None
        """
        with db_session.begin() as session:
            try:
                session.add(job_log)
                session.commit()
            except Exception as e:
                session.rollback()
                log.error(f"保存任务日志失败: {str(e)}")
            finally:
                session.close()

    @classmethod
    async def init_system_scheduler(cls) -> None:
        """
        应用启动时初始化定时任务。
    
        返回:
        - None
        """
        # 延迟导入避免循环导入
        from app.api.v1.module_application.job.crud import JobCRUD
        from app.api.v1.module_system.auth.schema import AuthSchema
        log.info('🔎 开始启动定时任务...')
        
        # 启动调度器
        scheduler.start()
        
        # 添加事件监听器
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)
        
        async with async_db_session() as session:
            async with session.begin():
                auth = AuthSchema(db=session)
                job_list = await JobCRUD(auth).get_obj_list_crud()
                
                # 只在一个实例上初始化任务
                # 使用Redis锁确保只有一个实例执行任务初始化
                import redis.asyncio as redis
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=int(settings.REDIS_PORT),
                    username=settings.REDIS_USER,
                    password=settings.REDIS_PASSWORD,
                    db=int(settings.REDIS_DB_NAME),
                )
                
                # 尝试获取锁，过期时间10秒
                lock_key = "scheduler_init_lock"
                lock_acquired = await redis_client.set(lock_key, "1", ex=10, nx=True)
                
                if lock_acquired:
                    try:
                        for item in job_list:
                            # 检查任务是否已经存在
                            existing_job = cls.get_job(job_id=item.id)
                            if existing_job:
                                cls.remove_job(job_id=item.id)  # 删除旧任务
                            
                            # 添加新任务
                            cls.add_job(item)
                            
                            # 根据数据库中保存的状态来设置任务状态
                            if hasattr(item, 'status') and item.status == "1":
                                # 如果任务状态为暂停，则立即暂停刚添加的任务
                                cls.pause_job(job_id=item.id)
                        log.info('✅️ 系统初始定时任务加载成功')
                    finally:
                        # 释放锁
                        await redis_client.delete(lock_key)
                else:
                    # 等待其他实例完成初始化
                    import asyncio
                    await asyncio.sleep(2)
                    log.info('✅️ 定时任务已由其他实例初始化完成')

    @classmethod
    async def close_system_scheduler(cls) -> None:
        """
        关闭系统定时任务。
    
        返回:
        - None
        """
        try:
            # 移除所有任务
            scheduler.remove_all_jobs()
            # 等待所有任务完成后再关闭
            scheduler.shutdown(wait=True)
            log.info('✅️ 关闭定时任务成功')
        except Exception as e:
            log.error(f'关闭定时任务失败: {str(e)}')

    @classmethod
    def get_job(cls, job_id: str | int) -> Job | None:
        """
        根据任务ID获取任务对象。
    
        参数:
        - job_id (str | int): 任务ID。
    
        返回:
        - Job | None: 任务对象，未找到则为 None。
        """
        return scheduler.get_job(job_id=str(job_id))

    @classmethod
    def get_all_jobs(cls) -> list[Job]:
        """
        获取全部调度任务列表。
    
        返回:
        - list[Job]: 任务列表。
        """
        return scheduler.get_jobs()

    @classmethod
    async def _task_wrapper(cls, func, job_id, *args, **kwargs):
        """任务执行包装器，添加分布式锁防止并发执行"""
        from redis.asyncio import Redis
        from app.config.setting import settings
        from app.core.logger import log

        # 使用项目配置创建Redis连接池
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            username=settings.REDIS_USER,
            password=settings.REDIS_PASSWORD,
            db=int(settings.REDIS_DB_NAME),
            encoding='utf-8',
            decode_responses=True,
            health_check_interval=20,
            max_connections=settings.POOL_SIZE,
            socket_timeout=settings.POOL_TIMEOUT
        )

        lock_key = f"job_lock:{job_id}"
        lock_expire = 30  # 锁过期时间，根据任务实际执行时间调整
        lock_acquired = None

        try:
            # 获取分布式锁，使用nx=True确保原子性操作
            lock_acquired = await redis_client.set(lock_key, "1", ex=lock_expire, nx=True)
            
            if lock_acquired:
                log.info(f"任务 {job_id} 获取执行锁成功")
                # 执行任务
                if iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    # 对于同步函数，使用线程池执行
                    log.info(f"任务 {job_id} 开始执行同步函数: {func.__name__}, 参数: {args}-{kwargs}")
                    try:
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(None, func, *args, **kwargs)
                        log.info(f"任务 {job_id} 同步函数执行完成，结果: {result}")
                        return result
                    except Exception as e:
                        log.error(f"任务 {job_id} 同步函数执行失败: {str(e)}")
                        raise
            else:
                # 获取锁失败，记录日志
                log.info(f"任务 {job_id} 获取执行锁失败，跳过本次执行")
                return None
        finally:
            # 释放锁
            if lock_acquired:
                await redis_client.delete(lock_key)
                log.info(f"任务 {job_id} 释放执行锁")
            # 关闭Redis连接
            await redis_client.close()

    @classmethod
    def add_job(cls, job_info: JobModel) -> Job:
        """
        根据任务配置创建并添加调度任务。

        参数:
        - job_info (JobModel): 任务对象信息（包含触发器、函数、参数等）。

        返回:
        - Job: 新增的任务对象。
        """
        # 动态导入模块
        # 1. 解析调用目标
        module_path, func_name = str(job_info.func).rsplit('.', 1)
        module_path = "app.api.v1.module_application.job.function_task." + module_path
        try:
            module = importlib.import_module(module_path)
            job_func = getattr(module, func_name)
            
            # 2. 确定任务存储器：优先使用redis，确保分布式环境中任务同步
            if job_info.jobstore is None:
                job_info.jobstore = 'redis'  # 改为默认使用redis存储
            
            # 3. 确定执行器
            job_executor = job_info.executor
            if job_executor is None:
                job_executor = 'default'
            
            # 异步函数必须使用默认执行器
            if iscoroutinefunction(job_func):
                job_executor = 'default'
            
            # 4. 创建触发器
            trigger = None
            if job_info.trigger is None or job_info.trigger.lower() == 'now':
                # 立即执行作业：省略trigger或使用'now'时，使用date触发器立即执行
                trigger = DateTrigger(run_date=datetime.now())
            elif job_info.trigger == 'date':
                if job_info.trigger_args is None:
                    raise ValueError("date触发器缺少执行时间参数")
                trigger = DateTrigger(run_date=job_info.trigger_args)
            elif job_info.trigger == 'interval':
                if job_info.trigger_args is None:
                    raise ValueError("interval触发器缺少参数")
                # 将传入的 interval 表达式拆分为不同的字段
                fields = job_info.trigger_args.strip().split()
                if len(fields) != 5:
                    raise ValueError("无效的 interval 表达式")
                second, minute, hour, day, week = tuple([int(field) if field != '*' else 0 for field in fields])
                # 秒、分、时、天、周（* * * * 1）
                trigger = IntervalTrigger(
                    weeks=week,
                    days=day,
                    hours=hour,
                    minutes=minute,
                    seconds=second,
                    start_date=job_info.start_date,
                    end_date=job_info.end_date,
                    timezone='Asia/Shanghai',
                    jitter=None
                )
            elif job_info.trigger == 'cron':
                if job_info.trigger_args is None:
                    raise ValueError("cron触发器缺少参数")
                # 秒、分、时、天、月、星期几、年 ()
                fields = job_info.trigger_args.strip().split()
                if len(fields) not in (6, 7):
                    raise ValueError("无效的 Cron 表达式")
                if not CronUtil.validate_cron_expression(job_info.trigger_args):
                    raise ValueError(f'定时任务{job_info.name}, Cron表达式不正确')

                parsed_fields = [None if field in ('*', '?') else field for field in fields]
                if len(fields) == 6:
                    parsed_fields.append(None)

                second, minute, hour, day, month, day_of_week, year = tuple(parsed_fields)
                trigger = CronTrigger(
                    second=second,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    year=year,
                    start_date=job_info.start_date,
                    end_date=job_info.end_date,
                    timezone='Asia/Shanghai'
                )
            else:
                raise ValueError("无效的 trigger 触发器")

            # 5. 添加任务（使用包装器函数）
            # 处理任务参数，确保空参数时返回空列表
            job_args = []
            if job_info.args:
                args_str = str(job_info.args).strip()
                if args_str:
                    job_args = args_str.split(',')
            
            job = scheduler.add_job(
                func=cls._task_wrapper,
                trigger=trigger,
                args=[job_func, str(job_info.id)] + job_args,
                kwargs=json.loads(job_info.kwargs) if job_info.kwargs else {},
                id=str(job_info.id),
                name=job_info.name,
                coalesce=job_info.coalesce,
                max_instances=1,  # 确保只有一个实例执行
                jobstore=job_info.jobstore,
                executor=job_executor,
            )
            log.info(f"任务 {job_info.id} 添加到 {job_info.jobstore} 存储器成功")
            return job
        except ModuleNotFoundError:
            raise ValueError(f"未找到该模块：{module_path}")
        except AttributeError:
            raise ValueError(f"未找到该模块下的方法：{func_name}")
        except Exception as e:
            raise CustomException(msg=f"添加任务失败: {str(e)}")

    @classmethod
    def remove_job(cls, job_id: str | int) -> None:
        """
        根据任务ID删除调度任务。
    
        参数:
        - job_id (str | int): 任务ID。
    
        返回:
        - None
        """
        query_job = cls.get_job(job_id=str(job_id))
        if query_job:
            scheduler.remove_job(job_id=str(job_id))

    @classmethod
    def clear_jobs(cls) -> None:
        """
        删除所有调度任务。
    
        返回:
        - None
        """
        scheduler.remove_all_jobs()

    @classmethod
    def modify_job(cls, job_id: str | int) -> Job:
        """
        更新指定任务的配置（运行中的任务下次执行生效）。
    
        参数:
        - job_id (str | int): 任务ID。
    
        返回:
        - Job: 更新后的任务对象。
    
        异常:
        - CustomException: 当任务不存在时抛出。
        """
        query_job = cls.get_job(job_id=str(job_id)) 
        if not query_job:
            raise CustomException(msg=f"未找到该任务：{job_id}")
        return scheduler.modify_job(job_id=str(job_id))

    @classmethod
    def pause_job(cls, job_id: str | int) -> None:
        """
        暂停指定任务（仅运行中可暂停，已终止不可）。

        参数:
        - job_id (str | int): 任务ID。

        返回:
        - None

        异常:
        - ValueError: 当任务不存在时抛出。
        """
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise ValueError(f"未找到该任务：{job_id}")
        scheduler.pause_job(job_id=str(job_id))

    @classmethod
    def resume_job(cls, job_id: str | int) -> None:
        """
        恢复指定任务（仅暂停中可恢复，已终止不可）。

        参数:
        - job_id (str | int): 任务ID。

        返回:
        - None

        异常:
        - ValueError: 当任务不存在时抛出。
        """
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise ValueError(f"未找到该任务：{job_id}")
        scheduler.resume_job(job_id=str(job_id))

    @classmethod
    def reschedule_job(cls, job_id: str | int, trigger=None, **trigger_args) -> Job | None:
        """
        重启指定任务的触发器。

        参数:
        - job_id (str | int): 任务ID。
        - trigger: 触发器类型
        - **trigger_args: 触发器参数

        返回:
        - Job: 更新后的任务对象

        异常:
        - CustomException: 当任务不存在时抛出。
        """
        query_job = cls.get_job(job_id=str(job_id))
        if not query_job:
            raise CustomException(msg=f"未找到该任务：{job_id}")
        
        # 如果没有提供新的触发器，则使用现有触发器
        if trigger is None:
            # 获取当前任务的触发器配置
            current_trigger = query_job.trigger
            # 重新调度任务，使用当前的触发器
            return scheduler.reschedule_job(job_id=str(job_id), trigger=current_trigger)
        else:
            # 使用新提供的触发器
            return scheduler.reschedule_job(job_id=str(job_id), trigger=trigger, **trigger_args)
    
    @classmethod
    def get_single_job_status(cls, job_id: str | int) -> str:
        """
        获取单个任务的当前状态。

        参数:
        - job_id (str | int): 任务ID

        返回:
        - str: 任务状态（'running' | 'paused' | 'stopped' | 'unknown'）
        """
        job = cls.get_job(job_id=str(job_id))
        if not job:
            return 'unknown'
        
        # 检查任务是否在暂停列表中
        if job_id in scheduler._jobstores[job._jobstore_alias]._paused_jobs:
            return 'paused'
        
        # 检查调度器状态
        if scheduler.state == 0:  # STATE_STOPPED
            return 'stopped'
        
        return 'running'

    @classmethod
    def print_jobs(cls,jobstore: Any | None = None, out: Any | None = None):
        """
        打印调度任务列表。
    
        参数:
        - jobstore (Any | None): 任务存储别名。
        - out (Any | None): 输出目标。
    
        返回:
        - None
        """
        scheduler.print_jobs(jobstore=jobstore, out=out)

    @classmethod
    def get_job_status(cls) -> str:
        """
        获取调度器当前状态。
    
        返回:
        - str: 状态字符串（'stopped' | 'running' | 'paused' | 'unknown'）。
        """
        #: constant indicating a scheduler's stopped state
        STATE_STOPPED = 0
        #: constant indicating a scheduler's running state (started and processing jobs)
        STATE_RUNNING = 1
        #: constant indicating a scheduler's paused state (started but not processing jobs)
        STATE_PAUSED = 2
        if scheduler.state == STATE_STOPPED:
            return 'stopped'
        elif scheduler.state == STATE_RUNNING:
            return 'running'
        elif scheduler.state == STATE_PAUSED:
            return 'paused'
        else:
            return 'unknown'

    @classmethod
    def run_job_now(cls, job_id: str | int) -> None:
        """
        立即执行指定任务。

        参数:
        - job_id (str | int): 任务ID。

        返回:
        - None

        异常:
        - ValueError: 当任务不存在时抛出。
        """
        job = cls.get_job(job_id=str(job_id))
        if not job:
            raise ValueError(f"未找到该任务：{job_id}")
        
        # 立即执行任务
        scheduler.modify_job(job_id=str(job_id), next_run_time=datetime.now())
        log.info(f"任务 {job_id} 已设置为立即执行")
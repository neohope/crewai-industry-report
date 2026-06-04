"""
超时管理和Kill工具
提供超时控制、任务kill、中断处理等功能
"""
import signal
import time
import threading
from functools import wraps
from datetime import datetime


class TimeoutException(Exception):
    """超时异常"""
    pass


class TimeoutManager:
    """超时管理器"""

    def __init__(self):
        self._timeout_handlers = {}
        self._start_times = {}
        self._active = True

    def start_timer(self, name, timeout_seconds):
        """启动计时器"""
        self._start_times[name] = datetime.now()
        print(f"[⏱️] 计时器 '{name}' 启动，超时: {timeout_seconds} 秒")

    def check_timeout(self, name, timeout_seconds):
        """检查是否超时"""
        if name not in self._start_times:
            return False

        elapsed = (datetime.now() - self._start_times[name]).total_seconds()
        if elapsed >= timeout_seconds:
            print(f"[⚠️] 计时器 '{name}' 超时！已运行 {elapsed:.1f} 秒")
            return True

        return False

    def get_elapsed(self, name):
        """获取已运行时间"""
        if name not in self._start_times:
            return 0
        return (datetime.now() - self._start_times[name]).total_seconds()

    def stop_timer(self, name):
        """停止计时器"""
        if name in self._start_times:
            elapsed = self.get_elapsed(name)
            print(f"[✅] 计时器 '{name}' 停止，运行: {elapsed:.1f} 秒")
            del self._start_times[name]

    def stop_all(self):
        """停止所有计时器"""
        for name in list(self._start_times.keys()):
            self.stop_timer(name)


class TimeoutContext:
    """超时上下文管理器（用于Windows兼容的超时）"""

    def __init__(self, seconds, timeout_message="操作超时"):
        self.seconds = seconds
        self.timeout_message = timeout_message
        self.timer = None
        self.timed_out = False

    def _timeout_handler(self):
        """超时处理函数"""
        self.timed_out = True
        print(f"[⚠️] {self.timeout_message}")

    def __enter__(self):
        """进入上下文"""
        self.timer = threading.Timer(self.seconds, self._timeout_handler)
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.timer:
            self.timer.cancel()
        if self.timed_out:
            raise TimeoutException(self.timeout_message)
        return False


def timeout(seconds, timeout_message="操作超时"):
    """
    超时装饰器（兼容Windows）

    用法:
        @timeout(300)  # 5分钟超时
        def long_running_task():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            error = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)

            if thread.is_alive():
                print(f"[⚠️] 函数 '{func.__name__}' 超时！超过 {seconds} 秒")
                raise TimeoutException(timeout_message)

            if error[0]:
                raise error[0]

            return result[0]
        return wrapper
    return decorator


class KillSwitch:
    """Kill开关 - 用于强制终止任务"""

    def __init__(self):
        self._killed = False
        self._kill_reason = None

    def trigger(self, reason="用户触发"):
        """触发kill"""
        print(f"[🛑] Kill开关触发: {reason}")
        self._killed = True
        self._kill_reason = reason

    def reset(self):
        """重置kill状态"""
        self._killed = False
        self._kill_reason = None

    def is_killed(self):
        """检查是否已触发kill"""
        return self._killed

    def check_kill(self):
        """检查kill状态，如果已触发则抛出异常"""
        if self._killed:
            raise Exception(f"任务已被kill: {self._kill_reason}")


# 全局实例
timeout_manager = TimeoutManager()
kill_switch = KillSwitch()


def safe_run(func, timeout_seconds, timeout_message="操作超时"):
    """
    安全运行函数，带超时保护

    参数:
        func: 要运行的函数
        timeout_seconds: 超时时间（秒）
        timeout_message: 超时时的提示信息

    返回:
        函数的返回值

    异常:
        TimeoutException: 超时时抛出
    """
    @timeout(timeout_seconds, timeout_message)
    def wrapped():
        return func()

    return wrapped()


def run_with_progress(func, timeout_seconds, check_interval=5):
    """
    带进度显示的运行

    参数:
        func: 要运行的函数
        timeout_seconds: 超时时间
        check_interval: 进度打印间隔（秒）
    """
    start_time = time.time()
    result = [None]
    error = [None]
    done = [False]

    def target():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
        done[0] = True

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    while not done[0]:
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            raise TimeoutException(f"超时！超过 {timeout_seconds} 秒")

        print(f"[⏳] 运行中... {elapsed:.1f} / {timeout_seconds} 秒")
        time.sleep(min(check_interval, timeout_seconds - elapsed))

    if error[0]:
        raise error[0]

    return result[0]

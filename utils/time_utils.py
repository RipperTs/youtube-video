"""时间工具：提供常用的时间格式转换函数。

仅使用标准库，避免额外依赖。
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_str_to_bj(utc_str: Optional[str], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """将UTC时间字符串转换为北京时间字符串。

    - 输入与输出格式均为 fmt（默认 "%Y-%m-%d %H:%M:%S"）
    - 解析失败时，返回原始输入
    - None 安全
    """
    if not utc_str:
        return utc_str
    try:
        utc_dt = datetime.strptime(utc_str, fmt).replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        return bj_dt.strftime(fmt)
    except Exception:
        return utc_str

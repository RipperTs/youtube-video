"""SQLite 数据库工具

职责：
- 提供全局的SQLite连接获取方法
- 初始化分析记录表（幂等）

依赖：使用内置 sqlite3，遵循 PEP 8
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

from config.settings import Config


def get_connection() -> sqlite3.Connection:
    """获取SQLite连接，自动创建数据库文件所在目录。

    Returns:
        sqlite3.Connection: 数据库连接，已设置 row_factory 为 Row
    """
    db_path = Config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库表（幂等）。"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_title TEXT,
                video_url TEXT NOT NULL,
                channel_name TEXT,
                cache_key TEXT,
                analysis_type TEXT,
                start_date TEXT,
                end_date TEXT,
                report_language TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_record(
    video_title: Optional[str],
    video_url: str,
    channel_name: Optional[str],
    cache_key: Optional[str],
    analysis_type: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    report_language: Optional[str],
) -> int:
    """插入一条分析记录。

    Args:
        video_title: 视频名称（可为空）
        video_url: 视频地址（必填）
        channel_name: 频道/ID 名称
        cache_key: 缓存 key
        analysis_type: 类型（单视频分析/批量分析）
        start_date: 分析开始日期
        end_date: 分析结束日期
        report_language: 报告语言

    Returns:
        int: 新记录的自增ID
    """
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO analysis_records (
                video_title, video_url, channel_name, cache_key,
                analysis_type, start_date, end_date, report_language, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (video_title or "").strip() or None,
                video_url,
                (channel_name or "").strip() or None,
                (cache_key or "").strip() or None,
                (analysis_type or "").strip() or None,
                (start_date or "").strip() or None,
                (end_date or "").strip() or None,
                (report_language or "").strip() or None,
                created_at,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


"""迁移脚本：将 cache/analysis 下的单视频缓存写入 SQLite 记录。

使用说明：
    python migrate_analysis_cache_to_db.py

规则：
- 仅处理 video_urls 长度为 1 的缓存文件（单视频），其余一律跳过
- 标题不从 JSON 中读取，写入时置为 None（由业务侧获取）
- 对于手动股票分析的复合URL（"url|symbol|start|end"），仅提取首段URL，日期按分段写入
- 若数据库中已存在相同 cache_key 的记录，则跳过，避免重复
"""

import json
import os
from typing import Optional, Tuple

from services.record_service import RecordService
from utils.db import get_connection, init_db


ANALYSIS_DIR = os.path.join("cache", "analysis")


def parse_single_video_entry(video_urls) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """解析单视频项，返回 (video_url, start_date, end_date)。

    - 普通单视频：video_urls=["https://..."]
    - 手动股票分析：video_urls=["https://...|SYMBOL|YYYY-MM-DD|YYYY-MM-DD"]
    """
    if not isinstance(video_urls, list) or not video_urls:
        return None, None, None
    entry = str(video_urls[0])
    if "|" in entry:
        parts = entry.split("|")
        video_url = parts[0].strip()
        start_date = parts[2].strip() if len(parts) > 2 and parts[2] else None
        end_date = parts[3].strip() if len(parts) > 3 and parts[3] else None
        return video_url, start_date, end_date
    return entry, None, None


def record_exists(cache_key: str) -> bool:
    """检查数据库是否已存在相同 cache_key 的记录。"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM analysis_records WHERE cache_key = ? LIMIT 1", (cache_key,))
        row = cur.fetchone()
        return row is not None
    finally:
        conn.close()


def migrate() -> None:
    init_db()
    svc = RecordService()

    if not os.path.isdir(ANALYSIS_DIR):
        print(f"未找到目录：{ANALYSIS_DIR}")
        return

    files = [f for f in os.listdir(ANALYSIS_DIR) if f.endswith(".json")]

    inserted, skipped_batch, skipped_invalid, skipped_exists = 0, 0, 0, 0

    for fname in files:
        fpath = os.path.join(ANALYSIS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            video_urls = data.get("video_urls", [])
            if not isinstance(video_urls, list) or len(video_urls) == 0:
                skipped_invalid += 1
                continue

            # 跳过批量（video_urls 多于1）
            if len(video_urls) > 1:
                skipped_batch += 1
                continue

            cache_key = data.get("cache_key")
            if not cache_key:
                skipped_invalid += 1
                continue

            if record_exists(cache_key):
                skipped_exists += 1
                continue

            video_url, start_date, end_date = parse_single_video_entry(video_urls)
            if not video_url:
                skipped_invalid += 1
                continue

            # 标题不要从JSON取，按需置空，由业务自动获取
            # 统一保存为“单视频分析”类型
            analysis_type = "单视频分析"

            # 尝试从 analysis_result 取语言（如无则置空）
            analysis_result = data.get("analysis_result", {}) or {}
            report_language = analysis_result.get("report_language")

            svc.add_record(
                video_url=video_url,
                channel_name=None,
                cache_key=cache_key,
                analysis_type=analysis_type,
                start_date=start_date,
                end_date=end_date,
                report_language=report_language,
            )
            inserted += 1

        except Exception as e:
            print(f"文件 {fname} 迁移失败: {e}")
            skipped_invalid += 1

    print(
        "迁移完成：\n"
        f"  新增记录: {inserted}\n"
        f"  已存在跳过: {skipped_exists}\n"
        f"  批量文件跳过: {skipped_batch}\n"
        f"  无效/失败: {skipped_invalid}"
    )


if __name__ == "__main__":
    migrate()


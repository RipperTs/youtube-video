"""记录服务：负责将分析记录写入SQLite

字段：
- 视频名称 video_title
- 视频地址 video_url
- 频道/ID名称 channel_name
- 缓存key cache_key
- 类型 analysis_type（单视频分析/批量分析）
- 分析开始日期 start_date
- 分析结束日期 end_date
- 报告语言 report_language
- 创建时间 created_at（UTC）
"""

from typing import Optional

from services.youtube_service import YouTubeService
from utils import db as db_util


class RecordService:
    """分析记录服务"""

    def __init__(self) -> None:
        # 确保表已初始化
        db_util.init_db()
        self.youtube_service = YouTubeService()

    def add_record(
            self,
            *,
            video_url: str,
            channel_name: Optional[str] = None,
            cache_key: Optional[str] = None,
            analysis_type: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            report_language: Optional[str] = None,
    ) -> int:
        video_detail = self.youtube_service.get_video_detail_by_url(video_url)

        """新增一条分析记录，返回记录ID。"""
        return db_util.insert_record(
            video_title=video_detail.get('title', 'Untitled'),
            video_url=video_url,
            channel_name=channel_name,
            cache_key=cache_key,
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
            report_language=report_language,
        )

import requests
from config.settings import Config


class YouTubeService:
    """YouTube数据服务"""

    def __init__(self):
        self.api_key = Config.TIKHUB_API_KEY
        self.base_url = Config.TIKHUB_BASE_URL

    def get_channel_videos(self, channel_id, count=20, next_token='', sort_by='newest'):
        """
        获取频道视频列表
        
        Args:
            channel_id: 频道ID或频道名称(@开头)
            count: 获取视频数量（每页）
            next_token: 下一页的令牌，用于分页
            sort_by: 排序方式 newest/oldest/mostPopular
        """
        url = f"{self.base_url}/youtube/web/get_channel_videos_v2"

        params = {
            'channel_id': channel_id,
            'lang': 'zh-CN',
            'sortBy': sort_by,
            'contentType': 'videos',
            'nextToken': next_token
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 获取视频数据
            video_data = data.get('data', {})
            videos = video_data.get('items', [])  # 根据示例，视频在items字段中
            next_token = video_data.get('nextToken', '')

            # 标准化视频数据格式
            formatted_videos = []
            for video in videos:
                if video.get('type') == 'video':
                    # 获取最佳缩略图
                    thumbnail_url = ''
                    thumbnails = video.get('thumbnails', [])
                    if thumbnails:
                        # 选择中等尺寸的缩略图
                        thumbnail_url = thumbnails[2]['url'] if len(thumbnails) > 2 else thumbnails[0]['url']

                    formatted_video = {
                        'id': video.get('id'),
                        'title': video.get('title'),
                        'description': video.get('title'),  # 使用标题作为描述
                        'url': f"https://www.youtube.com/watch?v={video.get('id')}",
                        'thumbnail': thumbnail_url,
                        'duration': video.get('lengthText', ''),
                        'published_at': video.get('publishedTimeText', ''),
                        'view_count': video.get('viewCountText', ''),
                        'is_live': video.get('isLiveNow', False)
                    }
                    formatted_videos.append(formatted_video)

            return {
                'videos': formatted_videos,
                'next_token': next_token,
                'has_more': bool(next_token)
            }

        except requests.RequestException as e:
            raise Exception(f"获取YouTube频道视频失败: {str(e)}")

    def extract_video_id(self, url):
        """从YouTube URL提取视频ID"""
        if 'youtube.com/watch?v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        else:
            raise ValueError("无效的YouTube URL")

    def get_video_detail_by_url(self, url):
        """通过视频URL获取视频详情"""
        video_id = self.extract_video_id(url)
        return self.get_video_details(video_id)

    def get_video_details(self, video_id):
        """
        获取视频详情数据
        :param video_id:
        :return:
        """
        url = 'https://api.tikhub.io/api/v1/youtube/web/get_video_info_v2?video_id=' + video_id
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            # 获取视频数据
            video_data = data.get('data', {}).get('videoDetails', {})
            return video_data
        except Exception as e:
            print(f"获取视频详情失败: {e}")
            return None


if __name__ == '__main__':
    yt_service = YouTubeService()
    detail = yt_service.get_video_detail_by_url('https://www.youtube.com/watch?v=GUrtlwWzt5g')
    print(detail)
class NotionConfig:
    API_BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2025-09-03"

    def __init__(self, notion_api_key: str) -> None:
        self.notion_api_key = notion_api_key

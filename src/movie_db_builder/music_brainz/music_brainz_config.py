class MusicBrainzConfig:
    BASE_URL = "https://musicbrainz.org/ws/2"

    def __init__(self, user_agent: str, auth_token: str, rate_limit: float = 1.0):
        self.user_agent: str = user_agent
        self.auth_token: str = auth_token
        self.rate_limit: int | float = rate_limit

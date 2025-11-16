class TMDBConfig:
    api_base_url = "https://api.themoviedb.org/3"

    def __init__(self, api_token: str):
        self.api_token = api_token

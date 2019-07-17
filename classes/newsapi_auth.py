from requests.auth import AuthBase



class NewsApiAuth(AuthBase):
    # Provided by newsapy: https://newsapi.org/docs/authentication
    def __init__(self, api_key: str):
        self.api_key = api_key

    def __call__(self):
        return get_auth_headers(self.api_key)


def get_auth_headers(api_key: str) -> dict:
    return {
        'Content-Type': 'Application/JSON',
        'Authorization': api_key
    }

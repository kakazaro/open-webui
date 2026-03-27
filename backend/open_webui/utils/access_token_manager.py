import requests
from requests.auth import HTTPBasicAuth
import time

from open_webui.env import (
    DATABRICKS_CLIENT_ID,
    DATABRICKS_CLIENT_SECRET,
)


class AccessTokenManager:
    def __init__(self, client_id: str = DATABRICKS_CLIENT_ID, client_secret: str = DATABRICKS_CLIENT_SECRET):
        self.access_token = None
        self.expires_at = None
        self.client_id = client_id
        self.client_secret = client_secret

    def get_access_token(self, url: str):
        if self.access_token is None or self.is_token_expired():
            self.refresh_token(url)
        return self.access_token

    def is_token_expired(self):
        if self.expires_at is None:
            return True
        return time.time() > self.expires_at

    def refresh_token(self, url: str):
        response = requests.post(f"{url.rsplit('/', 1)[0]}/oidc/v1/token",
                                 auth=HTTPBasicAuth(self.client_id, self.client_secret), data={
                'grant_type': 'client_credentials',
                'scope': 'all-apis'
            })

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.expires_at = time.time() + data['expires_in'] - 60  # subtract 1 minute to account for clock skew

        else:
            raise Exception(f"Failed to refresh token: {response.text}")

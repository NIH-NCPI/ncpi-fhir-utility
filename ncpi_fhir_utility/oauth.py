import logging
from datetime import datetime
import os
import requests
from requests.auth import AuthBase
import datetime

logger = logging.getLogger(__name__)


class OAuth(AuthBase):
    access_token: str
    expiration: datetime

    def __init__(self, url, client_id, client_secret, uma_audience):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.uma_audience = uma_audience
        self.refresh_token()

    def __call__(self, r):
        if self.expiration <= datetime.datetime.now():
            self.refresh_token()
        r.headers["authorization"] = "Bearer " + self.access_token
        return r

    def refresh_token(self):
        token = self.get_access_token()
        self.access_token = token['access_token']
        self.expiration = datetime.datetime.now() + datetime.timedelta(seconds=(token['expires_in'] - 10))

    def get_access_token(self):
        request_session = requests.Session()
        caCert = os.getenv('CONFIG__REQUESTS__CA')
        if caCert:
            request_session.verify = caCert

        response_access_token = request_session.post(
            self.url,
            data={'grant_type': 'client_credentials', 'client_id': self.client_id, 'client_secret': self.client_secret}
        )

        response_access_token.raise_for_status()

        if not self.uma_audience:
            return response_access_token.json()
        else:
            response = request_session.post(
                self.url,
                headers={'Authorization': f"Bearer {response_access_token.json()['access_token']}"},
                data={'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
                      'audience': self.uma_audience}
            )

            response.raise_for_status()
            return response.json()

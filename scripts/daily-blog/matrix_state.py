"""Private Matrix account-data storage for ephemeral scheduled workers."""
from urllib.parse import quote
import httpx


class MatrixKV:
    def __init__(self, homeserver, token, namespace):
        self.client = httpx.Client(headers={'Authorization': f'Bearer {token}'}, timeout=25)
        self.base = homeserver.rstrip('/') + '/_matrix/client/v3'
        response = self.client.get(self.base + '/account/whoami')
        self.check(response)
        self.user = response.json()['user_id']
        self.namespace = namespace

    @staticmethod
    def check(response):
        if not response.is_success:
            raise RuntimeError(f'Matrix API HTTP {response.status_code}')

    def url(self, key):
        return self.base + '/user/' + quote(self.user, safe='') + '/account_data/' + quote(self.namespace + '.' + key, safe='')

    def get(self, key):
        response = self.client.get(self.url(key))
        if response.status_code == 404:
            return None
        self.check(response)
        return response.json()

    def put(self, key, value):
        self.check(self.client.put(self.url(key), json=value))

    def send(self, room, text, transaction):
        return self.event(room, {'msgtype': 'm.text', 'body': text}, transaction)

    def event(self, room, payload, transaction):
        response = self.client.put(self.base + '/rooms/' + quote(room, safe='')
                                   + '/send/m.room.message/' + transaction,
                                   json=payload)
        self.check(response)
        return response.json()['event_id']


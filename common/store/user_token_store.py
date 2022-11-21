import time

token_temp = {}


class UserTokenStore(object):
    def __init__(self, key):
        """
        key is used to distinguish different Store，each app's accessToken is independent
        :param key:
        """
        self.key = key
        if self.key not in token_temp:
            token_temp[self.key] = {}

    def save(self, user_key, token, expires_in, create_time=None):
        """
        save user token
        :param user_key: user key
        :param token: token
        :param expires_in: how long the token is valid, unit is second
        :param create_time: if create_time is None, use current time
        :return:
        """
        current_time = time.time()
        token_dict = token_temp[self.key]
        token_dict[user_key] = {
            'token': token,
            'expires_in': expires_in,
            'update_time': current_time,
            'create_time': create_time or current_time
        }

    def get(self, user_key):
        """
        if token is expires, clear it and return None
        :return:
        :param user_key: user key
        """
        token_dict = token_temp[self.key]
        if user_key in token_dict:
            token = token_dict[user_key]
            if time.time() - token['update_time'] > token['expires_in']:
                token_dict.pop(user_key)
                return None
            return token['token']
        return None

    def refresh(self, user_key, expires_in):
        """
        refresh token if it exists
        :param user_key: user key
        :param expires_in: how long the token is valid, unit is second
        :return:
        """
        if self.key in token_temp:
            token_dict = token_temp[self.key]
            if user_key in token_dict:
                self.save(user_key, token_dict[user_key]['token'], expires_in, token_dict[user_key]['create_time'])

    @staticmethod
    def clean(key):
        """
        clean token by key
        :param key: string
        :return:
        """
        if key in token_temp:
            token_temp.pop(key)

    @staticmethod
    def clean_all():
        """
        clean all token
        :return:
        """
        for key in token_temp:
            token_temp.pop(key)
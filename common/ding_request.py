import aiohttp
from urllib import parse

from .token_store import TokenStore


def check_response_error(response, error_code=0, error_msg_key='errmsg'):
    if response['errcode'] != error_code:
        raise Exception(response[error_msg_key])


def join_url(base_url, *args):
    if not args:
        return base_url
    return parse.urljoin(base_url, ''.join(args))


class DingRequest(object):
    url_prefix = 'https://oapi.dingtalk.com'

    def __init__(self, app_key, app_secret):
        """
        set Dingtalk app_key and app_secret
        :param app_key: Dingtalk app app_key
        :param app_secret: Dingtalk app app_secret
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.token_store = TokenStore(app_key)

    async def refresh_token(self):
        """
        refresh token if it expires
        :return:
        """
        current_token = self.token_store.get()
        if not current_token:
            token = await self.get_token()
            self.token_store.save(token['token'], token['expires_in'])

    async def latest_token(self):
        """
        get latest token
        :return:
        """
        await self.refresh_token()
        return self.token_store.get()

    @staticmethod
    async def get_response(url, params=None, response_callback=None):
        """
        get response from server
        :param url: url join with url_prefix
        :param params:
        :param response_callback: response callback function
        :return:
        """
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url, params=params) as response:
                return await response_callback(response) if response_callback else await response.json()

    @staticmethod
    async def post_response(url, json, data=None, response_callback=None):
        """
        post response to server, if json is not None, use json, else use data
        :param url: url join with url_prefix
        :param data: json data
        :param json: form data
        :param response_callback: response callback function
        :return:
        """
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.post(url, json=json, data=data) as response:
                return await response_callback(response) if response_callback else await response.json()

    async def get_token(self):
        """
        get token from server
        :return:
        """
        response = await self.get_response(join_url(self.url_prefix, 'gettoken'), {
            'appkey': self.app_key,
            'appsecret': self.app_secret
        })
        check_response_error(response)
        return {
            'token': response['access_token'],
            'expires_in': response['expires_in']
        }

    async def get_auth_scopes(self):
        """
        get auth scopes
        :return:
        """
        response = await self.get_response(
            join_url(self.url_prefix, f'auth/scopes?access_token={await self.latest_token()}'))
        check_response_error(response)
        return {
            'auth_user_field': response['auth_user_field'],
            'auth_org_scopes': response['auth_org_scopes']
        }

    async def department_listsubid(self, dept_id=None):
        """
        get department listsubid
        :param dept_id: department id
        :return:
        """
        response = await self.post_response(
            join_url(self.url_prefix, f'topapi/v2/department/listsubid?access_token={await self.latest_token()}'), {
                'dept_id': dept_id
            })
        check_response_error(response)
        return response['result']['dept_id_list']

    async def department_detail(self, dept_id, language='zh_CN'):
        """
        get department detail
        :param dept_id: department id
        :param language: language
        :return:
        """
        assert dept_id is not None, 'dept_id is required'
        response = await self.post_response(
            join_url(self.url_prefix, f'topapi/v2/department/get?access_token={await self.latest_token()}'), {
                'dept_id': dept_id,
                'language': language
            })
        check_response_error(response)
        return response['result']

    async def department_users(self, dept_id, cursor=0, size=100, language='zh_CN', contain_access_limit=False):
        """
        get department users
        :param dept_id: department id
        :param cursor: offset
        :param size: size
        :param language: language
        :param contain_access_limit: Whether to return an employee with restricted access
        :return:
        """
        assert dept_id is not None, 'dept_id is required'
        response = await self.post_response(
            join_url(self.url_prefix, f'topapi/v2/user/list?access_token={await self.latest_token()}'), {
                'dept_id': dept_id,
                'cursor': cursor,
                'size': size,
                'language': language,
                'contain_access_limit': contain_access_limit
            })
        check_response_error(response)
        return response['result']


def ding_request_instance(app_key, app_secret):
    """
    if you want to use custom DingRequest class or Store class, you can set monkey patch to this function
    :param app_key:
    :param app_secret:
    :return:
    """
    return DingRequest(app_key, app_secret)

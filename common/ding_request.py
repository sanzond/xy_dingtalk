import base64
import hmac
import time

import aiohttp
from urllib import parse

from .store.token_store import TokenStore
from .store.user_token_store import UserTokenStore


def get_sign(data, key):
    """
    signature for dingtalk request
    :param data:
    :param key:
    """
    sign = base64.b64encode(
        hmac.new(key.encode('utf-8'), str(data).encode('utf-8'), digestmod='SHA256').digest())
    return str(sign, 'utf-8')


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
    async def get_response(url, params=None, response_callback=None, **kwargs):
        """
        get response from server
        :param url: url join with url_prefix
        :param params:
        :param response_callback: response callback function
        :return:
        """
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url, params=params, **kwargs) as response:
                return await response_callback(response) if response_callback else await response.json()

    @staticmethod
    async def post_response(url, json, data=None, response_callback=None, **kwargs):
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
            async with session.post(url, json=json, data=data, **kwargs) as response:
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

    async def get_user_access_token(self, app_key, app_secret, temp_auth_code):
        """
        get user access token
        :param app_key: Dingtalk app app_key
        :param app_secret: Dingtalk
        :param temp_auth_code: temporary authorization code
        :return: {"expireIn":7200,"accessToken":"xx","refreshToken":"xx"}
        """
        response = await self.post_response('https://api.dingtalk.com/v1.0/oauth2/userAccessToken', {
            "clientSecret": app_secret,
            "clientId": app_key,
            "code": temp_auth_code,
            "grantType": "authorization_code"
        })
        if response.get('code') is not None:
            raise Exception(response['message'])
        return response

    async def get_user_info_by_access_token(self, user_access_token, union_id='me'):
        """
        get user info with user access_token
        :param user_access_token: user_access_token, not app access_token
        :param union_id: info whose union_id is this, self is 'me'
        :return:
        """
        response = await self.get_response(
            f'https://api.dingtalk.com/v1.0/contact/users/{union_id}',
            headers={
                'x-acs-dingtalk-access-token': user_access_token
            }
        )
        if response.get('code') is not None:
            raise Exception(response['message'])
        return response

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

# -*- coding: utf-8 -*-
import asyncio
from urllib import parse

from odoo import http
from odoo.http import request, route

from ..common.ding_request import join_url, ding_request_instance


class DingTalkController(http.Controller):
    scan_oauth_url = 'https://open.work.weixin.qq.com/wwopen/sso/qrConnect?appid={corp_id}&agentid={agentid}&redirect_uri={redirect_uri}'
    web_oauth_url = 'https://login.dingtalk.com/oauth2/auth?redirect_uri={redirect_uri}&response_type=code&client_id={client_id}&scope={scope}&prompt=consent'

    @classmethod
    def force_authenticate(cls, session, user):
        session.pre_uid = user.id
        session.pre_login = user.login
        if not user._mfa_url():
            session.finalize(request.env)
        user._update_last_login()

    @route('/ding/oauth2/info', type='json', auth='public')
    def get_ding_oauth2_info(self, app_id, redirect_uri=None):
        """
        get info for build DingTalk login info
        :param app_id:
        :param redirect_uri: redirect url after login, don't need host
        :return:
        """
        app = request.env['dingtalk.app'].sudo().browse(int(app_id))
        host = request.httprequest.host_url
        return {
            'client_id': app.app_key,
            'redirect_uri': join_url(host, f'ding/oauth2/login/{app_id}') if redirect_uri is None else
            join_url(host, redirect_uri)
        }

    async def test_api(self, ding_request):
        with open('/Users/admin/workspace/python_project/odoo-16/test_addons/dingtalk/static/all_users.png', 'rb') as f:
            content = f.read()
            print(ding_request.upload_media('image', content, 'all_users.png'))

    @route('/ding/oauth2/login/<int:app_id>', type='http', auth='public')
    def login_by_oauth2(self, authCode, app_id):
        """
        login by dingtalk oauth2
        :param authCode:
        :param app_id:
        :return:
        """
        app = request.env['dingtalk.app'].sudo().browse(int(app_id))
        ding_request = ding_request_instance(app.app_key, app.app_secret)

        async def _get_user_info():
            access_token = (await ding_request.get_user_access_token(app.app_key, app.app_secret, authCode))[
                'accessToken']
            return await ding_request.get_user_info_by_access_token(access_token)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        get_user_info = loop.create_task(_get_user_info())
        loop.run_until_complete(get_user_info)
        loop.close()

        user_info = get_user_info.result()
        employee = request.env['hr.employee'].sudo().search([('ding_id', '=', user_info['unionId'])])
        if employee.user_id.id:
            self.force_authenticate(request.session, employee.user_id)
            return request.redirect('/web')

    @route('/ding/oauth2/build/<string:oauth_type>/<int:app_id>', type='http', auth='public')
    def ding_oauth2(self, oauth_type, app_id, scope='openid'):
        """
        build dingtalk oauth2 url
        :param oauth_type: scan or web, scan is build to qrcode, web is build to redirect url
        :param app_id: authenticate used app id
        :param scope: openid or openid corpid
        :return:
        """
        oauth2_info = self.get_ding_oauth2_info(app_id)
        client_id = oauth2_info['client_id']
        redirect_uri = parse.quote(oauth2_info['redirect_uri'])

        _redirect_uri = ''
        if oauth_type == 'scan':
            _redirect_uri = self.scan_oauth_url.format(
                agentid=client_id,
                redirect_uri=redirect_uri
            )
        elif oauth_type == 'web':
            _redirect_uri = self.web_oauth_url.format(
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=scope
            )
        return request.redirect(_redirect_uri, 303, False)

    @route('/ding/test', type='http', auth='public')
    def test_api(self):
        print(request.env['hr.employee'].send_ding_message(1, [
            '124143586123834203', '092416520435324730'
        ], msg={
            "msgtype": "text",
            "text": {
                "content": "月会通知"
            }
        }))


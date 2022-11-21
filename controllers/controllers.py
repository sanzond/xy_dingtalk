# -*- coding: utf-8 -*-
import asyncio
from urllib import parse

from odoo import http
from odoo.http import request, route

from ..common.ding_request import join_url, ding_request_instance


class DingTalkController(http.Controller):
    scan_oauth_url = 'https://open.work.weixin.qq.com/wwopen/sso/qrConnect?appid={corp_id}&agentid={agentid}&redirect_uri={redirect_uri}'
    web_oauth_url = 'https://oapi.dingtalk.com/connect/oauth2/sns_authorize?redirect_uri={redirect_uri}&response_type=code&appid={app_key}&scope={scope}'

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
            'app_key': app.app_key,
            'redirect_uri': join_url(host, f'ding/oauth2/login/{app_id}') if redirect_uri is None else
            join_url(host, redirect_uri)
        }

    @route('/ding/oauth2/login/<int:app_id>', type='http', auth='public')
    def login_by_oauth2(self, code, app_id):
        """
        login by dingtalk oauth2
        :param code:
        :param app_id:
        :return:
        """
        app = request.env['dingtalk.app'].sudo().browse(int(app_id))
        ding_request = ding_request_instance(app.app_key, app.app_secret)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        get_userid_task = loop.create_task(ding_request.get_user_info(app.app_key, app.app_secret, code))
        loop.run_until_complete(get_userid_task)
        loop.close()
        # we_id = get_userid_task.result()
        # employee = request.env['hr.employee'].sudo().search([('we_id', '=', we_id)])
        # if employee.user_id.id:
        #     secret_dict = {
        #         'npa': True,
        #         'type': 'we',
        #         'password': CustomEncrypt.encrypt(ResUsers.we_auth_secret)
        #     }
        #     request.session.authenticate(request.session.db, employee.user_id.login, secret_dict)
        #     return request.redirect('/web')
        print(code)
        print(app_id)

    @route('/ding/oauth2/build/<string:oauth_type>/<int:app_id>', type='http', auth='public')
    def ding_oauth2(self, oauth_type, app_id, scope='snsapi_login'):
        """
        build dingtalk oauth2 url
        :param oauth_type: scan or web, scan is build to qrcode, web is build to redirect url
        :param app_id: authenticate used app id
        :param scope: openid or openid corpid
        :return:
        """
        oauth2_info = self.get_ding_oauth2_info(app_id)
        app_key = oauth2_info['app_key']
        redirect_uri = parse.quote(oauth2_info['redirect_uri'])

        _redirect_uri = ''
        if oauth_type == 'scan':
            _redirect_uri = self.scan_oauth_url.format(
                agentid=app_key,
                redirect_uri=redirect_uri
            )
        elif oauth_type == 'web':
            _redirect_uri = self.web_oauth_url.format(
                app_key=app_key,
                redirect_uri=redirect_uri,
                scope=scope
            )
        return request.redirect(_redirect_uri, 303, False)

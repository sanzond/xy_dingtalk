import asyncio
import datetime
import threading
import time
import traceback

from odoo import models, fields, api
from odoo.tools.translate import _

from ..common.ding_request import ding_request_instance


def get_now_time_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class App(models.Model):
    _name = 'dingtalk.app'
    _description = 'Dingtalk App'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    agentid = fields.Char(string='Agent ID', required=True)
    app_key = fields.Char(string='AppKey', required=True)
    app_secret = fields.Char(string='AppSecret', required=True)

    sync_with_user = fields.Boolean(string='Sync with res.user', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    # callback settings
    token = fields.Char(string='Token')
    encoding_aes_key = fields.Char(string='EncodingAESKey')

    def run_ding_sync(self):
        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
            'title': 'Sync Start......',
            'message': _('Start sync organization now, please wait......'),
            'warning': True
        })

        # create a threading to avoid odoo ui blocking
        def _sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.run(self.sync_ding_organization())

        thread = threading.Thread(target=_sync)
        thread.start()

    async def sync_ding_organization(self):
        start = time.time()
        uid = self.env.uid
        is_success = True
        with self.env.registry.cursor() as new_cr:
            self.env = api.Environment(new_cr, uid, self.env.context)

            detail_log = f'start sync at {get_now_time_str()}......'
            try:
                ding_request = ding_request_instance(self.app_key, self.app_secret)

                # get dingtalk auth scope
                auth_scopes = await ding_request.get_auth_scopes()

                await self.env['hr.department'].with_context(
                    self.env.context, ding_app=self, ding_request=ding_request,
                    auth_scopes=auth_scopes
                ).sync_ding_department()
                detail_log += f'\nsync success!'
            except Exception:
                is_success = False
                detail_log += f'\nsync failed, error: \n{traceback.format_exc()}'
            finally:
                detail_log += f'\nsync end at {get_now_time_str()}, cost {round(time.time() - start, 2)}s'
                company_id = self.company_id.id
                self.env['dingtalk.log'].create({
                    'company_id': company_id,
                    'ding_app_id': self.id,
                    'detail': detail_log
                })
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                    'title': 'Sync End......',
                    'message': f'Sync organization end, {"success" if is_success else "failed"}',
                    'warning': True if is_success else False
                })
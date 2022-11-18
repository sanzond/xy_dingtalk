from odoo import models, fields


class DingtalkLog(models.Model):
    _name = 'dingtalk.log'
    _description = 'Dingtalk Log'
    _order = 'create_date desc'

    company_id = fields.Many2one('res.company', string='Company')
    ding_app_id = fields.Many2one('dingtalk.app', string='Dingtalk App')
    detail = fields.Text(string='Detail')

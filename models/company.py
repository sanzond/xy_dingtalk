from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    ding_app_ids = fields.One2many('dingtalk.app', 'company_id', string='Dingtalk Apps')

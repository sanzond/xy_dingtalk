from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    app_ids = fields.One2many('dingtalk.app', 'company_id', string='Apps')

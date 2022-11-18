# -*- coding: utf-8 -*-
# from odoo import http


# class Dingtalk(http.Controller):
#     @http.route('/dingtalk/dingtalk', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dingtalk/dingtalk/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dingtalk.listing', {
#             'root': '/dingtalk/dingtalk',
#             'objects': http.request.env['dingtalk.dingtalk'].search([]),
#         })

#     @http.route('/dingtalk/dingtalk/objects/<model("dingtalk.dingtalk"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dingtalk.object', {
#             'object': obj
#         })

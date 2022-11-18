from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    ding_id = fields.Char(string='Dingtalk User ID')
    ding_department_ids = fields.Many2many('hr.department', 'ding_employee_department_rel', 'employee_id',
                                           'department_id', string='Dingtalk Departments')
    ding_extattr = fields.Json(string='Dingtalk User Extattr')

    @api.depends('department_id.manager_id')
    def _compute_parent_id(self):
        for employee in self.filtered('department_id.manager_id'):
            employee.parent_id = employee.department_id.manager_id

    def write_with_user(self, val):
        if self.user_id.id is False:
            user = self.env['res.users'].create({
                'name': val['name'],
                'login': val['ding_id'],
                'company_id': val['company_id'],
                'company_ids': [(4, val['company_id'])],
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
                'active': val['active']
            })
            val['user_id'] = user.id
        else:
            self.user_id.write({
                'name': val['name'],
                'active': val['active']
            })
        self.write(val)

    def create_with_user(self, val_list):
        for val in val_list:
            user = self.env['res.users'].search([('login', '=', val['ding_id']), ('active', 'in', [True, False])])
            if user.id is False:
                user = self.env['res.users'].create({
                    'name': val['name'],
                    'login': val['ding_id'],
                    'company_id': val['company_id'],
                    'company_ids': [(4, val['company_id'])],
                    'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
                    'active': val['active']
                })
            val['user_id'] = user.id

        return self.create(val_list)

    async def sync_user(self, ding_department, server_dep_id):
        ding_request = self.env.context.get('ding_request')
        ding_app = self.env.context.get('ding_app')
        sync_with_user = ding_app.sync_with_user

        users = await ding_request.department_users(server_dep_id)
        # users has multipage, so we need get all users
        next_cursor = users.get('next_cursor', None)

        user_list = users['list']
        while next_cursor is not None:
            _users = await ding_request.department_users(server_dep_id, cursor=next_cursor)
            next_cursor = _users.get('next_cursor', None)
            user_list.extend(_users['list'])

        create_users = []
        manager_id = None

        for user in user_list:
            # job
            title = user.get('title', None)
            job = self.env['hr.job'].search(
                [('name', '=', title), ('company_id', '=', ding_app.company_id.id)])
            if title and job.id is False:
                job = self.env['hr.job'].create({
                    'name': title,
                    'company_id': ding_app.company_id.id
                })

            employee = self.search([('ding_id', '=', user['unionid']), ('active', 'in', [True, False])])
            main_department = ding_department.search([('ding_id', '=', user['dept_id_list'][0])])

            modify_data = {
                'name': user['name'],
                'ding_id': user['unionid'],
                'company_id': ding_app.company_id.id,
                'department_id': main_department.id,
                'ding_department_ids': [(4, ding_department.id)],
                'job_id': job.id,
                'work_email': user.get('email', None),
                'mobile_phone': user.get('mobile', None),
                'ding_extattr': user.get('extension', None),
                'parent_id': False,
                'active': user['active']
            }

            if employee.id is False:
                modify_data['marital'] = False
                create_users.append(modify_data)
            else:
                employee.write_with_user(modify_data) if sync_with_user else employee.write(modify_data)

            # set department manager
            if user['leader'] == 1 and not manager_id:
                manager_id = user['unionid']

        if len(create_users) > 0:
            # create users limit 500
            limit = 500
            for i in range(0, len(create_users), limit):
                create_vals = create_users[i:i + limit]
                # if config set not sync user, not create user
                self.create_with_user(create_vals) if sync_with_user else self.create(create_vals)
        if manager_id:
            ding_department.write({'manager_id': self.search([('ding_id', '=', manager_id)]).id})

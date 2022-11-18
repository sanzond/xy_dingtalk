import asyncio

from odoo import models, fields


class Department(models.Model):
    _inherit = 'hr.department'

    ding_id = fields.Char(string='Dingtalk Department ID')
    ding_parent_id = fields.Char(string='Dingtalk Parent Department ID')
    ding_order = fields.Integer(string='Dingtalk Department Order')
    '''because a Dingtalk user can have multi departments, so we need a many2many field, 
    the department_id field is only main department'''
    ding_employee_ids = fields.Many2many('hr.employee', 'ding_employee_department_rel', 'department_id', 'employee_id',
                                         string='Dingtalk Employees')

    async def get_server_depart_tree(self, dep_ids, for_in_callback=None):
        """
        get Dingtalk server department id tree
        :param dep_ids: server department id list
        :param for_in_callback: callback function in for loop
        :return:
        """
        ding_request = self.env.context.get('ding_request')
        tree = []

        _tasks = []

        async def _append_to_tree(parent_dep_id, _tree):
            sublist = await ding_request.department_listsubid(parent_dep_id)
            _tree.append({
                'id': parent_dep_id,
                'children': await self.get_server_depart_tree(sublist, for_in_callback)
            })

        for dep_id in dep_ids:
            if for_in_callback:
                for_in_callback(dep_id)
            _tasks.append(_append_to_tree(dep_id, tree))

        await asyncio.gather(*_tasks)

        return tree

    async def sync_department(self):
        """
        sync department from Dingtalk server
        :return:
        """
        ding_request = self.env.context.get('ding_request')
        ding_app = self.env.context.get('ding_app')
        auth_scopes = self.env.context.get('auth_scopes')

        dep_ding_id_list = []
        depart_tree = await self.get_server_depart_tree(
            auth_scopes['auth_org_scopes']['authed_dept'],
            lambda dep_id: dep_ding_id_list.append(dep_id)
        )

        tasks = []

        # change where the employee in the department status to active = False
        self.env['hr.employee'].search([('ding_department_ids.ding_id', 'in', dep_ding_id_list)]).write(
            {'active': False})

        async def _sync_dep(_dep_leaf, parent_id):
            _tasks = []
            dep_detail = await ding_request.department_detail(_dep_leaf['id'])

            dep = self.search([('ding_id', '=', dep_detail['dept_id'])])
            # dep need commit to db because sync user need use it
            modify_data = {
                'company_id': ding_app.company_id.id,
                'name': dep_detail['name'],
                'ding_id': dep_detail['dept_id'],
                'ding_parent_id': dep_detail.get('parent_id', None),  # root department has no parent_id
                'parent_id': parent_id,
                'ding_order': dep_detail['order'],
                'manager_id': False
            }

            if dep.id is False:
                dep = self.create(modify_data)
            else:
                dep.write(modify_data)

            await self.env['hr.employee'].sync_user(dep, dep_detail['dept_id'])

            if len(_dep_leaf['children']) > 0:
                for child in _dep_leaf['children']:
                    _tasks.append(_sync_dep(child, dep.id))
                await asyncio.gather(*_tasks)

        for dep_leaf in depart_tree:
            tasks.append(_sync_dep(dep_leaf, False))

        await asyncio.gather(*tasks)

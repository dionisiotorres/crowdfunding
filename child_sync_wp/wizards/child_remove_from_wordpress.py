# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields


class ChildRemoveFromWordpress(models.TransientModel):
    _name = 'child.remove.from.wordpress.wizard'

    child_ids = fields.Many2many(
        'compassion.child', compute='_get_active_ids',
        string='Selected children', default=lambda c: c._get_active_ids()
    )

    def _get_active_ids(self):
        children = self.env['compassion.child'].browse(
            self.env.context.get('active_ids'))
        valid_children = children.filtered(lambda c: c.state == 'I')
        for wizard in self:
            wizard.child_ids = valid_children
        return valid_children

    @api.multi
    def remove_child_from_internet(self):
        return self.child_ids.remove_from_wordpress()

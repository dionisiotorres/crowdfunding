# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    description = fields.Text(compute='_compute_description')
    project_title = fields.Char(compute='_compute_project_title')

    @api.multi
    def _compute_description(self):
        lang_map = {
            'fr_CH': 'desc_fr',
            'de_DE': 'desc_de',
            'en_US': 'desc_en',
            'it_IT': 'desc_it',
        }
        for child in self:
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            try:
                child.description = getattr(child, lang_map.get(lang))
            except:
                child.description = False

    def _compute_project_title(self):
        for child in self:
            firstname = child.firstname or ''
            lang_map = {
                'fr_CH': u"À propos du centre d'accueil",
                'de_DE': u"Über %s's Projekt" % firstname,
                'en_US': firstname + u"'s Project",
                'it_IT': u'Project',
            }
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            child.project_title = lang_map.get(lang)

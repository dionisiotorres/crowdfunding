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
from datetime import datetime

from openerp import api, models, fields


class CompassionHold(models.Model):
    """ Send Communication when Hold Removal is received. """
    _inherit = 'compassion.hold'

    no_money_extension_duration = fields.Integer(
        compute='_compute_no_money_extension_duration')

    @api.multi
    def _compute_no_money_extension_duration(self):
        """
        Gets the default No Money hold extension duration
        :return: integer: hold duration in days
        """
        settings = self.env['availability.management.settings']
        for hold in self:
            if hold.no_money_extension < 2:
                hold.no_money_extension_duration = settings.get_param(
                    'no_money_hold_duration')
            else:
                hold.no_money_extension_duration = settings.get_param(
                    'no_money_hold_extension')

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        ids = super(CompassionHold, self).beneficiary_hold_removal(
            commkit_data)
        job_obj = self.env['partner.communication.job']
        now = datetime.now()
        for hold in self.browse(ids).filtered(
                lambda h: h.channel in ('ambassador', 'event') and
                fields.Datetime.from_string(h.expiration_date) > now):
            communication_type = self.env.ref(
                'partner_communication_switzerland.hold_removal')
            job_obj.create({
                'config_id': communication_type.id,
                'partner_id': hold.primary_owner.partner_id.id,
                'object_ids': hold.id,
                'user_id': communication_type.user_id.id,
            })
            if hold.ambassador:
                job_obj.create({
                    'config_id': communication_type.id,
                    'partner_id': hold.ambassador.id,
                    'object_ids': hold.id,
                    'user_id': communication_type.user_id.id,
                })

        return ids

    @api.multi
    def postpone_no_money_hold(self, additional_text=None):
        """
        Send a communication to sponsor for reminding the payment.
        TODO: Attach a payment slip
        :param additional_text: text to add in the notification to hold owner
        :return: None
        """
        failed = self.env[self._name]
        # Last reminder: cancellation notice
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_3')
        failed += self.filtered(
            lambda h: h.no_money_extension > 1)._send_hold_reminder(
            communication_type)

        # Second reminder
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_2')
        failed += self.filtered(
            lambda h: h.no_money_extension == 1)._send_hold_reminder(
            communication_type)

        # First reminder
        communication_type = self.env.ref(
            'partner_communication_switzerland.'
            'sponsorship_waiting_reminder_1')
        failed += self.filtered(
            lambda h: h.no_money_extension == 0)._send_hold_reminder(
            communication_type)

        if failed:
            # Send warning to Admin users
            self.env['mail.mail'].create({
                'subject': 'URGENT: Postpone no money holds failed!',
                'author_id': self.env.user.partner_id.id,
                'recipient_ids': [(6, 0, [18000, 13])],
                'body_html': 'These holds should be urgently verified: <br/>'
                '<br/>' + ', '.join(failed.mapped('hold_id'))
            }).send()

    def _send_hold_reminder(self, communication):
        """
        Sends the hold reminder communication to sponsors and postpone the
        hold.
        :param communication: the type of communication
        :return: recordset of failed updated holds.
        """
        notification_text = "\n\nA reminder has been prepared for the " \
            "sponsor {} ({})"
        sponsorships = self.env['recurring.contract'].with_context(
            default_auto_send=False)
        failed = self.env[self._name]
        for hold in self.filtered('child_id.sponsorship_ids'):
            sponsorship = hold.child_id.sponsorship_ids[0]
            sponsor = hold.child_id.sponsor_id
            # Filter sponsorships where we wait for the bank authorization
            if sponsorship.state == 'mandate' and sponsor.bank_ids:
                try:
                    super(CompassionHold, hold).postpone_no_money_hold()
                    hold.no_money_extension -= 1
                    continue
                except:
                    failed += hold
                    continue
            # Cancel old invoices
            if len(sponsorship.due_invoice_ids) > 1:
                for invoice in sponsorship.due_invoice_ids[:-1]:
                    invoice.signal_workflow('invoice_cancel')
            try:
                super(CompassionHold, hold).postpone_no_money_hold(
                    notification_text.format(sponsor.name, sponsor.ref))
                sponsorships += sponsorship
            except:
                failed += hold
        sponsorships.send_communication(communication, correspondent=False)
        return failed

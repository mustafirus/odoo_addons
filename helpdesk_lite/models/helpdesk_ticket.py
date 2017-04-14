# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import re

from odoo.exceptions import AccessError


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Tickets"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['helpdesk.stage'].search("", order='sequence', limit=1)

    name = fields.Char(string='Ticket', track_visibility='always', required=True)
    description = fields.Text('Private Note')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', index=True)
    contact_name = fields.Char('Contact Name')
    email_from = fields.Char('Email', help="Email address of the contact", index=True)
    user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange', index=True, default=False)
    team_id = fields.Many2one('helpdesk.team', string='Support Team', track_visibility='onchange',
        default=lambda self: self.env['helpdesk.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, help='When sending mails, the default email address is taken from the support team.')
    date_deadline = fields.Datetime(string='Deadline', track_visibility='onchange')

    stage_id = fields.Many2one('helpdesk.stage', string='Stage', index=True, track_visibility='onchange',
                               domain="[]",
                               copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Urgent')], 'Priority', index=True, default='1', track_visibility='onchange')
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')], string='Kanban State', track_visibility='onchange',
                                    required=True, default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this ticket\n
                                           * Ready for next stage indicates the ticket is ready to go to next stage""")

    color = fields.Integer('Color Index')
    legend_blocked = fields.Char(related="stage_id.legend_blocked", string='Kanban Blocked Explanation', readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", string='Kanban Valid Explanation', readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", string='Kanban Ongoing Explanation', readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(name=_('%s (copy)') % (self.name))
        return super(HelpdeskTicket, self).copy(default=default)

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(HelpdeskTicket, self).message_get_suggested_recipients()
        try:
            for tic in self:
                if tic.partner_id:
                    tic._message_add_suggested_recipient(recipients, partner=tic.partner_id, reason=_('Customer'))
                elif tic.email_from:
                    tic._message_add_suggested_recipient(recipients, email=tic.email_from, reason=_('Customer Email'))
        except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        # remove default author when going through the mail gateway. Indeed we
        # do not want to explicitly set user_id to False; however we do not
        # want the gateway user to be responsible if no other responsible is
        # found.
        contact_name, email_from =  re.match(r"(.*) *<(.*)>", msg.get('from')).group(1,2)
        body = tools.html2plaintext(msg.get('body'))
        bre = re.match(r"(.*)^-- *$", body, re.MULTILINE|re.DOTALL|re.UNICODE)
        if bre:
            desc = bre.group(1)
        defaults = {
            'name':  msg.get('subject') or _("No Subject"),
            'email_from': email_from,
            'contact_name': contact_name,
            'description':  desc or body,
        }

        create_context = dict(self.env.context or {})
        # create_context['default_user_id'] = False
        # create_context.update({
        #     'mail_create_nolog': True,
        # })

        if custom_values:
            defaults.update(custom_values)

        return super(HelpdeskTicket, self.with_context(create_context)).message_new(msg, custom_values=defaults)
        # res_id = super(HelpdeskTicket, self.with_context(create_context)).message_new(msg, custom_values=defaults)
        # tic = self.browse(res_id)
        # email_list = tools.email_split(email_from)
        # partner_ids = filter(None, tic._find_partner_from_emails(email_list))
        # tic.message_subscribe(partner_ids)
        # return res_id

    @api.model
    def create(self, vals):

        partner_id = vals.get('partner_id')
        email_from = vals.get('email_from')
        if not partner_id:
            partner = self.env['res.partner'].sudo().search([('email', '=ilike', email_from)], limit=1)
            partner_id = partner.id
            if partner_id:
                vals.update({
                    'partner_id': partner_id,
                })
                del vals['contact_name']
        # if partner_id:
        #     vals.update({
        #         'message_follower_ids': [(4, partner_id)]
        #         })

        context = dict(self.env.context)
        context.update({
            'mail_create_nosubscribe': True,
        })
        # self.message_subscribe([partner_id])
        return super(HelpdeskTicket, self.with_context(context)).create(vals)


    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            # vals.update(vals['stage_id'])
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        # user_id change: update date_open
        # if vals.get('user_id') and 'date_open' not in vals:
        #     vals['date_open'] = fields.Datetime.now()
        return super(HelpdeskTicket, self).write(vals)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def takeit(self):
        self.ensure_one()
        vals = {'user_id' : self.env.uid,
                'team_id': self.env['helpdesk.team'].sudo()._get_default_team_id(user_id=self.env.uid).id}
        return super(HelpdeskTicket, self).write(vals)




        # res_id = super(HelpdeskTicket, self.with_context(context)).create(vals)
        # tic = self.browse(res_id)
        # email_list = tools.email_split(email_from)
        # partner_ids = filter(None, tic._find_partner_from_emails(email_list))
        # tic.message_subscribe()
        # return res_id

        # partner = self.env['res.partner'].sudo().browse(partner_id)
        # if partner_id:
        #     vals['message_follower_ids'] = [partner,]
        # email_list = issue.email_split(msg)
        #  partner_ids = filter(None, issue._find_partner_from_emails(email_list))




        # if vals.get('user_id') and not vals.get('date_open'):
        #     vals['date_open'] = fields.Datetime.now()
        # if 'stage_id' in vals:
        #     vals.update(vals['stage_id'])

        # context: no_log, because subtype already handle this
        # context['mail_create_nolog'] = True

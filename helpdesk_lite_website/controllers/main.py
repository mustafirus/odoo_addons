# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, _
from odoo.addons.website_portal.controllers.main import website_account
from odoo.http import request


class WebsiteAccount(website_account):

    def _prepare_portal_layout_values(self):
        values = super(WebsiteAccount, self)._prepare_portal_layout_values()
        # domain is needed to hide non portal project for employee
        # portal users can't see the privacy_visibility, fetch the domain for them in sudo
        ticket_count = request.env['helpdesk.ticket'].search_count([])
        values.update({
            'ticket_count': ticket_count,
        })
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_tickets(self, page=1, date_begin=None, date_end=None, project=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()

        sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }

        domain = ([])
        order = sortings.get(sortby, sortings['date'])['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('helpdesk.ticket', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # pager
        pager = request.website.pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=values['ticket_count'],
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        helpdesk_ticket = request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'sortings': sortings,
            'sortby': sortby,
            'tickets': helpdesk_ticket,
            'page_name': 'ticket',
            'archive_groups': archive_groups,
            'default_url': '/my/tickets',
            'pager': pager
        })
        return request.render("helpdesk_website.my_tickets", values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True)
    def my_tickets_ticket(self, ticket_id=None, **kw):
        ticket = request.env['helpdesk.ticket'].browse(ticket_id)
        return request.render("helpdesk_website.my_tickets_ticket", {'ticket': ticket})

    @http.route(['/helpdesk/submit'], type='http', auth="public", website=True)
    def new_ticket(self, **kw):
        if(request.session.uid):
            user = request.env.user
            vals = {
                'partner_id': request.session.uid,
            }
        else:
            vals = {
                'partner_id': None,
            }

        return request.render("website.new_ticket", vals)

    @http.route(['/helpdesk'], type='http', auth="public", website=True)
    def helpdesk(self, **kw):
        team = http.request.env.ref('helpdesk.team_alpha')
        team.website_published = False
        return request.render("helpdesk.helpdesk",{ 'use_website_helpdesk_form' : True,
                                                    'team': team,
                                                    })
        # teams = http.request.env['helpdesk.team']
        # return request.render("helpdesk.helpdesk",{ 'teams' : teams,
        #                                             'team': team,
        #                                             'use_website_helpdesk_form' : True })


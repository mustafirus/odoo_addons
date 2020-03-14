# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        # domain is needed to hide non portal project for employee
        # portal users can't see the privacy_visibility, fetch the domain for them in sudo
        ticket_count = request.env['helpdesk_lite.ticket'].search_count([])
        values.update({
            'ticket_count': ticket_count,
        })
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        groupby = 'none'  # kw.get('groupby', 'project') #TODO master fix this
        values = self._prepare_portal_layout_values()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
#            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        # searchbar_filters = {
        #     'all': {'label': _('All'), 'domain': []},
        #     'open': {'label': _('Opened'), 'domain': [('stage_id.code', '=', 'open')]},
        #     'wait': {'label': _('Wait for user'), 'domain': [('stage_id.code', '=', 'wait')]},
        #     'close': {'label': _('Closed'), 'domain': [('stage_id.code', '=', 'close')]},
        # }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
#            'customer': {'input': 'customer', 'label': _('Search in Customer')},
#             'stage': {'input': 'stage', 'label': _('Search in Stages')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        # searchbar_groupby = {
        #     'none': {'input': 'none', 'label': _('None1')},
        #     'stage': {'input': 'stage', 'label': _('Stage')},
        # }

        domain = ([])

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        # if not filterby:
        #     filterby = 'wait'
        # domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('helpdesk_lite.ticket', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        ticket_count = request.env['helpdesk_lite.ticket'].search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            # url_args={'date_begin': date_begin, 'date_end': date_end},
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        helpdesk_ticket = request.env['helpdesk_lite.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            # 'date': date_begin,
            # 'date_end': date_end,
            'tickets': helpdesk_ticket,
            'page_name': 'ticket',
            # 'archive_groups': archive_groups,
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            # 'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            # 'new': HelpdeskTicket.website_form

            # 'groupby': groupby,
            # 'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            # 'filterby': filterby,
        })
        return request.render("helpdesk_lite.portal_my_tickets", values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True)
    def my_tickets_ticket(self, ticket_id=None, **kw):
        ticket = request.env['helpdesk_lite.ticket'].browse(ticket_id)
        return request.render("helpdesk_lite.my_tickets_ticket", {'ticket': ticket})

    @http.route(['/helpdesk/new'], type='http', auth="public", website=True)
    def ticket_new(self, **kw):
        pri = request.env['helpdesk_lite.ticket'].fields_get(allfields=['priority'])['priority']['selection']
        pri_default = '1'
        if(request.session.uid):
            # user = request.env.user
            vals = {
                'loggedin': True,
                'priorities': pri,
                'priority_default': pri_default,
            }
        else:
            vals = {
                'loggedin': False,
                'priorities': pri,
                'priority_default': pri_default,
            }

        return request.render("helpdesk_lite.new_ticket", vals)


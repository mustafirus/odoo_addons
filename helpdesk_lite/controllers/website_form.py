from odoo import http
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.http import request


class ContactController(WebsiteForm):

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'helpdesk_lite.ticket':
            if request.session.uid:
                request.params['partner_id'] = request.env.user.partner_id.id

        return super(ContactController, self).website_form(model_name, **kwargs)

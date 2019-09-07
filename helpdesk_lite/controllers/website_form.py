from odoo import http
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.http import request


class ContactController(WebsiteForm):

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'helpdesk_lite.ticket':
            if request.uid:
                partner_id = request.env.user.commercial_partner_id
                request.params['partner_id'] = partner_id
                if partner_id.user_id:
                    request.params['user_id'] = partner_id.user_id

        return super(ContactController, self).website_form(model_name, **kwargs)

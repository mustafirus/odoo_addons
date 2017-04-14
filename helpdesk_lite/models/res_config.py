import string
from glob import glob

from odoo import models, fields, api, _
from odoo.service.db import dump_db, exp_drop, restore_db
from odoo.exceptions import AccessError
import os
import errno
import odoo
from os.path import expanduser

class HelpdeskConfig(models.TransientModel):
    _name = 'helpdesk.config.settings'
    _inherit = 'res.config.settings'

    default_name = fields.Char('Default ticket name', default_model='helpdesk.ticket')
    module_helpdesk_lite_website = fields.Boolean("Publish on website", help='Installs module helpdesk_website')



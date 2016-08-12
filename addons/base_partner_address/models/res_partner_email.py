# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, an open source suite of business apps
# This module copyright (C) 2015 bloopark systems (<http://bloopark.de>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models

EMAIL_ADDRESS_TYPES = [
    ('private', 'Private'),
    ('business', 'Business'),
    ('other', 'Other'),
]


class ResPartnerEmail(models.Model):
    _name = 'res.partner.email'
    _inherit = ['res.partner.preferred']

    name = fields.Char('Email', required=True)
    type = fields.Selection(EMAIL_ADDRESS_TYPES, 'Type',
                            default='private', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
                                 ondelete='cascade', index=True)
    preferred = fields.Boolean('Preferred')

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'The email must be unique in the system!')
    ]

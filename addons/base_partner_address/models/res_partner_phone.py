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

PHONE_TYPES = [
    ('phone', 'Phone'),
    ('fax', 'Fax'),
    ('mobile', 'Mobile'),
    ('other', 'Other'),
]


class ResPartnerPhone(models.Model):

    _name = 'res.partner.phone'

    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
                                 ondelete='cascade', index=True)
    type = fields.Selection(PHONE_TYPES, 'Type',
    						default='mobile', required=True)
    name = fields.Char('Number', required=True)

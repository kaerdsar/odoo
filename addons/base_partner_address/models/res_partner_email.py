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
from openerp import fields, models, api

EMAIL_ADDRESS_TYPES = [
    ('private', 'Private'),
    ('business', 'Business'),
    ('other', 'Other'),
]


class ResPartnerEmail(models.Model):

    """Add model for new partner email handling."""

    _name = 'res.partner.email'

    name = fields.Char('Email', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
                                 ondelete='cascade', index=True)
    type = fields.Selection(EMAIL_ADDRESS_TYPES, 'Type', required=True)
    preferred = fields.Boolean('Preferred')

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'The email must be unique in the system!')
    ]

    @api.model
    def create(self, vals):
        """Update preferred email for related partner in addition."""
        if vals.get('name', False):
            name = vals.get('name', False)
            vals.update({'name': name.lower()})
        rec = super(ResPartnerEmail, self).create(vals)
        if rec.preferred:
            rec.set_partner_preferred_email(rec.partner_id, rec.name)
        return rec

    @api.multi
    def write(self, vals):
        """Update preferred email for related partner in addition."""
        if vals.get('name', False):
            name = vals.get('name', False)
            vals.update({'name': name.lower()})
        res = super(ResPartnerEmail, self).write(vals)
        for rec in self:
            if vals.get('preferred', False) or (vals.get('name', False) and
                                                rec.preferred):
                rec.set_partner_preferred_email(rec.partner_id, rec.name)
        return res

    @api.multi
    def unlink(self):
        """In addition clean preferred email data in partner."""
        update_partner_email = []
        for rec in self:
            update_partner_email.append(rec.partner_id)
        res = super(ResPartnerEmail, self).unlink()

        for partner in update_partner_email:
            if len(partner.partner_email_ids) == 0:
                partner.write({
                    'preferred_email': False,
                    'email': '',
                })

        return res

    def set_partner_preferred_email(self, partner, email_address):
        """Set preferred email address for given partner."""
        partner.write({
            'preferred_email': self.id,
            'email': email_address,
        })

        return True

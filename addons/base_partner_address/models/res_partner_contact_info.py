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
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class ResPartnerContactInfo(models.AbstractModel):
    _name = 'res.partner.contact.info'

    def get_contact_type(self):
        return self._name.split('.')[-1]

    @api.model
    def create(self, vals):
        """Update preferred for related partner in addition."""
        if vals.get('preferred', False) and vals.get('partner_id', False):
            self.clean_preferred(vals['partner_id'])
        rec = super(ResPartnerContactInfo, self).create(vals)
        if rec.preferred:
            rec.set_partner_preferred(rec.partner_id)
        return rec

    @api.multi
    def write(self, vals):
        """Update preferred for related partner in addition."""
        if vals.get('preferred', False):
            for rec in self:
                self.clean_preferred(rec.partner_id.id)
        res = super(ResPartnerContactInfo, self).write(vals)
        for rec in self:
            if rec.preferred:
                rec.set_partner_preferred(rec.partner_id)
        return res

    @api.multi
    def unlink(self):
        """In addition clean preferred data in partner."""
        partners = []
        for rec in self:
            partners.append(rec.partner_id)
        res = super(ResPartnerContactInfo, self).unlink()

        contact_type = self.get_contact_type()
        field_ids = 'partner_%s_ids' % contact_type
        field = 'preferred_%s' % contact_type
        values = {field : False}
        if hasattr(self.env['res.partner'], contact_type):
            values.update({contact_type: False})

        for partner in partners:
            contacts = getattr(partner, field_ids)
            if len(contacts) == 0 or len(contacts.filtered('preferred')) == 0:
                partner.write(values)
        return res

    def clean_preferred(self, partner_id):
        """Set preferred flag for all partner to False."""
        contacts = self.search(
            [('preferred', '=', True),
             ('partner_id', '=', partner_id)])
        if contacts:
            contacts.write({'preferred': False})
        return True

    def set_partner_preferred(self, partner):
        """Set preferred for given partner."""
        contact_type = self.get_contact_type()
        field = 'preferred_%s' % contact_type
        values = {field : self.id}
        if hasattr(self.env['res.partner'], contact_type):
            values.update({contact_type: self.name})
        return partner.write(values)

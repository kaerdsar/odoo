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
from openerp import api, fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    street = fields.Char(compute='_get_address_data',
                         inverse='_set_address_data')
    street2 = fields.Char(compute='_get_address_data',
                          inverse='_set_address_data')
    zip = fields.Char(compute='_get_address_data', inverse='_set_address_data')
    city = fields.Char(compute='_get_address_data',
                       inverse='_set_address_data')
    state_id = fields.Many2one(compute='_get_address_data',
                               inverse='_set_address_data')
    country_id = fields.Many2one(compute='_get_address_data',
                                 inverse='_set_address_data')
    email = fields.Char(compute='_get_address_data',
                        inverse='_set_address_data', store=True)
    phone = fields.Char(compute='_get_address_data',
                        inverse='_set_address_data', store=True)
    fax = fields.Char(compute='_get_address_data', inverse='_set_address_data')

    @api.depends('partner_id')
    def _get_address_data(self):
        """Read address, phone and email functional fields."""
        for rec in self:
            street = street2 = zip = city = email = phone = fax = ''
            state_id = country_id = False
            if rec.partner_id:
                address = rec.partner_id.preferred_address
                if address:
                    street = address.street
                    street2 = address.street2
                    zip = address.zip
                    city = address.city
                    state_id = address.state_id and \
                        address.state_id.id or False
                    country_id = address.country_id and \
                        address.country_id.id or False
                email = rec.partner_id.email
                phone_rec = rec.partner_id.get_phone('phone')
                if phone_rec:
                    phone = phone_rec.name
                fax_rec = rec.partner_id.get_phone('fax')
                if fax_rec:
                    fax = fax_rec.name

            rec.street = street
            rec.street2 = street2
            rec.zip = zip
            rec.city = city
            rec.email = email
            rec.phone = phone
            rec.fax = fax
            rec.state_id = state_id
            rec.country_id = country_id

    def _set_address_data(self):
        """Write address, phone and email functional fields."""
        for rec in self:
            if rec.partner_id:
                # add / update address data
                address = rec.partner_id.preferred_address
                address_data = {
                    'street': rec.street,
                    'street2': rec.street2,
                    'zip': rec.zip,
                    'city': rec.city,
                    'state_id': rec.state_id and rec.state_id.id or False,
                    'country_id': rec.country_id and rec.country_id.id or False
                }
                if address:
                    address.write(address_data)
                else:
                    address_data.update({
                        'name': rec.partner_id.name,
                        'type': 'business',
                        'partner_id': rec.partner_id.id
                    })
                    self.env['res.partner.address'].create(address_data)

                # add / update email data
                email_rec = self.env['res.partner.email'].sudo().search(
                    [('partner_id', '=', rec.partner_id.id),
                     ('name', '=', rec.email), ('type', '=', 'business')],
                    limit=1)
                email_data = {
                    'name': rec.email
                }
                if email_rec:
                    email_rec.write(email_data)
                else:
                    if rec.partner_id.partner_email_ids:
                        rec.partner_id.partner_email_ids.write(
                            {'preferred': False})
                    email_data.update({
                        'type': 'business',
                        'partner_id': rec.partner_id.id,
                        'preferred': True
                    })
                    self.env['res.partner.email'].create(email_data)

                # add / update phone data
                phone_rec = rec.partner_id.get_phone('phone')
                phone_data = {
                    'name': rec.phone
                }
                if phone_rec:
                    phone_rec.write(phone_data)
                else:
                    phone_data.update({
                        'type': 'phone',
                        'partner_id': rec.partner_id.id
                    })
                    self.env['res.partner.phone'].create(phone_data)

                # add / update fax data
                fax_rec = rec.partner_id.get_phone('fax')
                fax_data = {
                    'name': rec.fax
                }
                if fax_rec:
                    fax_rec.write(fax_data)
                else:
                    fax_data.update({
                        'type': 'fax',
                        'partner_id': rec.partner_id.id
                    })
                    self.env['res.partner.phone'].create(fax_data)

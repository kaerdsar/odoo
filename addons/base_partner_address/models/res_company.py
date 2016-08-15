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
                         inverse='_set_address_street')
    street2 = fields.Char(compute='_get_address_data',
                          inverse='_set_address_street2')
    zip = fields.Char(compute='_get_address_data', inverse='_set_address_zip')
    city = fields.Char(compute='_get_address_data',
                       inverse='_set_address_city')
    state_id = fields.Many2one(compute='_get_address_data',
                               inverse='_set_address_state_id')
    country_id = fields.Many2one(compute='_get_address_data',
                                 inverse='_set_address_country_id')
    email = fields.Char(compute='_get_address_data',
                        inverse='_set_email_data', store=True)
    phone = fields.Char(compute='_get_address_data',
                        inverse='_set_phone_phone', store=True)
    fax = fields.Char(compute='_get_address_data', inverse='_set_phone_fax')

    @api.depends('partner_id')
    def _get_address_data(self):
        """Read address, phone and email functional fields."""
        for rec in self:
            if rec.partner_id:
                address = rec.partner_id.preferred_address
                if address:
                    rec.street = address.street
                    rec.street2 = address.street2
                    rec.postcode = address.zip
                    rec.city = address.city
                    rec.state_id = address.state_id and \
                        address.state_id.id or False
                    rec.country_id = address.country_id and \
                        address.country_id.id or False
                phone_rec = rec.partner_id.get_phone('phone')
                fax_rec = rec.partner_id.get_phone('fax')
                rec.phone = phone_rec and phone_rec.name or ''
                rec.fax = fax_rec and fax_rec.name or ''
                rec.email = rec.partner_id.email

    def _set_address_street(self):
        for rec in self:
            rec._set_address_data('street', rec.street)

    def _set_address_street2(self):
        for rec in self:
            rec._set_address_data('street2', rec.street2)

    def _set_address_zip(self):
        for rec in self:
            rec._set_address_data('zip', rec.zip)

    def _set_address_city(self):
        for rec in self:
            rec._set_address_data('city', rec.city)

    def _set_address_state_id(self):
        for rec in self:
            rec._set_address_data('state_id', rec.state_id)

    def _set_address_country_id(self):
        for rec in self:
            rec._set_address_data('country_id', rec.country_id)

    def _set_address_data(self, name, value):
        if name in ['state_id', 'country_id']:
            value = value.id
        address = self.partner_id.preferred_address
        if address:
            address.write({name: value})
            if address.is_empty():
                address.unlink()
        else:
            self.env['res.partner.address'].create({
                'partner_id': self.partner_id.id,
                'type': 'business',
                'preferred': True,
                name: value
            })

    def _set_phone_phone(self):
        for rec in self:
            rec._set_phone_data('phone', rec.phone)

    def _set_phone_fax(self):
        for rec in self:
            rec._set_phone_data('fax', rec.fax)

    def _set_phone_data(self, phone_type, value):
        phone_rec = self.partner_id.get_phone(phone_type)
        if phone_rec and not value:
            phone_rec.unlink()
        elif phone_rec and value:
            phone_rec.write({'name': value})
        elif not phone_rec and value:
            self.env['res.partner.phone'].create({
                'partner_id': self.partner_id.id,
                'type': phone_type,
                'name': value
            })

    def _set_email_data(self):
        for rec in self:
            email = rec.email
            email_rec = self.env['res.partner.email'].sudo().search(
                [('partner_id', '=', rec.partner_id.id),
                 ('type', '=', 'business')])
            if email_rec and not email:
                email_rec.unlink()
                if rec.partner_id.partner_email_ids:
                    rec.partner_id.partner_email_ids[0].write({
                        'preferred': True
                    })
            elif email_rec and email:
                email_rec.write({'name': email})
            elif not email_rec and email:
                if rec.partner_id.partner_email_ids:
                    rec.partner_id.partner_email_ids.write(
                        {'preferred': False})
                self.env['res.partner.email'].create({
                    'partner_id': rec.partner_id.id,
                    'type': 'business',
                    'preferred': True,
                    'name': email
                })

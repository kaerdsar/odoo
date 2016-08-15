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
from openerp import api, models

ADDRESS_FIELDS = ['street', 'street2', 'zip', 'city', 'state_id', 'country_id']
EMAIL_FIELDS = ['email']
PHONE_FIELDS = ['phone', 'fax', 'mobile']


class BasePartnerAddressMigration(models.TransientModel):
    _name = 'base.partner.address.migration'

    def build_domain(self, contact_fields):
    	domain = []
    	for field in contact_fields:
    		if len(domain) != 0:
    			domain.insert(0, '|')
    		domain.append((field, '!=', False))
    	return domain

    def build_values(self, partner, contact_fields):
    	values = {'preferred': True}
    	for field in contact_fields:
    		if field.endswith('_id'):
    			obj = getattr(partner, field)
    			values[field] = obj and obj.id or False
    		else:
    			values[field] = getattr(partner, field)
    	return values

    @api.model
    def migrate_contact_information(self):
    	partner_obj = self.env['res.partner']

    	addres_obj = self.env['res.partner.address']
    	domain = self.build_domain(ADDRESS_FIELDS)
    	for partner in partner_obj.search(domain):
    		values = self.build_values(partner, ADDRESS_FIELDS)
    		address = addres_obj.search([('partner_id', '=', partner.id)])
    		if address:
    			address.write(values)
    		else:
    			values.update({'partner_id': partner.id})
    			address = addres_obj.create(values)

    	email_obj = self.env['res.partner.email']
    	domain = self.build_domain(EMAIL_FIELDS)
    	for partner in partner_obj.search(domain):
    		values = {'name': partner.email, 'preferred': True}
    		email = email_obj.search([('partner_id', '=', partner.id)])
    		if email:
    			email.write(values)
    		else:
    			values.update({'partner_id': partner.id})
    			email = email_obj.create(values)

    	phone_obj = self.env['res.partner.phone']
    	domain = self.build_domain(PHONE_FIELDS)
    	for partner in partner_obj.search(domain):
    		for field in PHONE_FIELDS:
    			if getattr(partner, field):
		    		values = {'name': getattr(partner, field), 'type': field}
		    		if field == 'phone':
		    			values['preferred'] = True
		    		phone = phone_obj.search([
		    			('partner_id', '=', partner.id),
		    			('type', '=', field)
		    		])
		    		if phone:
		    			phone.write(values)
		    		else:
		    			values.update({'partner_id': partner.id})
		    			phone = phone_obj.create(values)

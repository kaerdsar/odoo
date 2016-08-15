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

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')
ADDRESS_TYPES = [('default', 'Default'), ('invoice', 'Invoice'),
                 ('delivery', 'Shipping'), ('contact', 'Contact'),
                 ('other', 'Other')]


class ResPartnerAddress(models.Model):
    _name = 'res.partner.address'
    _rec_name = 'partner_id'
    _inherit = ['res.partner.preferred']

    type = fields.Selection(ADDRESS_TYPES, 'Address Type', default='default',
                            required=True)
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', 'State',
                               ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    use_company_address = fields.Boolean('Use Company Address')
    display_name = fields.Char(compute='_get_display_name', string='Name',
                               store=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
                                 ondelete='cascade', index=True)
    partner_is_company = fields.Boolean(related='partner_id.is_company')
    preferred = fields.Boolean('Preferred')

    @api.depends('partner_id', 'type')
    def _get_display_name(self):
        """Return address display name."""
        for rec in self:
            rec.display_name = rec._name_get()

    @api.onchange('use_company_address')
    def onchange_use_company_address(self):
        if self.use_company_address and self.partner_id and \
                self.partner_id.parent_id:
            address = self.search(
                [('type', '=', self.type),
                 ('partner_id', '=', self.partner_id.parent_id.id)])
            if address:
                self.street = address.street
                self.street2 = address.street2
                self.zip = address.zip
                self.city = address.city
                self.state_id = address.state_id
                self.country_id = address.country_id

    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id

    def _name_get(self):
        """Add address type and company name to display address name."""
        address_type = self.type
        if address_type:
            address_type = dict(self.fields_get(allfields=['type'])
                                ['type']['selection'])[self.type]
        name = '(%s)' % _(address_type)
        if self.partner_id:
            name = '%s %s' % (self.partner_id.name, name)
            if self.partner_id.parent_id:
                name = '%s, %s' % (self.partner_id.parent_id.name, name)
        return name

    @api.multi
    def name_get(self):
        """Update address display name in address selections."""
        res = []
        for rec in self:
            res.append((rec.id, rec._name_get()))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('display_name', 'ilike', name)] + args,
                               limit=limit)
        if not recs:
            recs = self.search([('partner_id.name', operator, name)] + args,
                               limit=limit)
        return recs.name_get()

    def search(self, cr, user, args, offset=0, limit=None, order=None,
               context=None, count=False):
        """Update default search.

        We have to update the search field which is used as _rec_name.
        Otherwise the search will take much more time.
        """
        if not args:
            args = []

        new_args = []
        for arg in args:
            new_arg = arg
            if len(arg) == 3 and arg[0] == 'partner_id' and arg[1] == 'ilike':
                new_arg = ('partner_id.name', arg[1], arg[2])
            new_args.append(new_arg)

        return super(ResPartnerAddress, self).search(
            cr, user, new_args, offset=offset, limit=limit, order=order,
            context=context, count=count)

    def _address_fields(self, cr, uid, context=None):
        """Return list of address."""
        return list(ADDRESS_FIELDS)

    def is_empty(self):
        """Check if address has no address data."""
        if not self.street and not self.street2 and not self.zip and \
                not self.city and not self.state_id and not self.country_id:
            return True
        return False

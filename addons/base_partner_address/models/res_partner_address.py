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
import simplejson
from openerp import _, api, fields, models

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')


class ResPartnerAddress(models.Model):

    _name = 'res.partner.address'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
                                 ondelete='cascade', index=True)
    type = fields.Selection([
        ('private', 'Private'),
        ('business', 'Business'),
        ('other', 'Other')], 'Address Type',
        default='private', required=True)
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', 'State',
                               ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    use_company_address = fields.Boolean('Use Company Address')
    address = fields.Char(compute='_get_json_address',
                          inverse='_set_json_address', string='Address')
    display_name = fields.Char(compute='_get_display_name', string='Name',
                               store=True)
    preferred = fields.Boolean('Preferred')

    # these fields are only for temporary usage because they will be extracted
    # and migrated later in LROERP-2737
    phone = fields.Char('Phone')
    fax = fields.Char('Fax')
    mobile = fields.Char('Mobile')

    @api.depends('street', 'street2', 'zip', 'city', 'country_id')
    def _get_json_address(self):
        for rec in self:
            country = rec.country_id or self.env.ref('base.de')
            address = {
                'street': rec.street or '',
                'street2': rec.street2 or '',
                'zip': rec.zip or '',
                'city': rec.city or '',
                'country_id': [country.id, country.name]
            }
            rec.address = simplejson.dumps(address)

    def _set_json_address(self):
        for rec in self:
            values = {
                'street': False,
                'street2': False,
                'zip': False,
                'city': False,
                'country_id': False
            }
            if rec.address:
                address = simplejson.loads(rec.address)
                values['street'] = address['street']
                values['street2'] = address['street2']
                values['zip'] = address['zip']
                values['city'] = address['city']
                if address['country_id']:
                    try:
                        if isinstance(address['country_id'], list):
                            values['country_id'] = int(address['country_id'][0])
                        else:
                            values['country_id'] = int(address['country_id'])
                    except ValueError:
                        values['country_id'] = False
            rec.write(values)

    @api.depends('partner_id', 'type')
    def _get_display_name(self):
        """Return address display name."""
        for rec in self:
            rec.display_name = rec._name_get()

    @api.onchange('use_company_address')
    def onchange_use_company_address(self):
        return {}

    @api.onchange('state_id')
    def onchange_state_id(self):
        return {}

    @api.onchange('type')
    def onchange_type(self):
        """Trigger the default values for the business address."""
        for rec in self:
            if rec.type == 'business' and rec.partner_id and \
                    rec.partner_id.parent_id:
                address = rec.search(
                    [('type', '=', rec.type),
                     ('partner_id', '=', rec.partner_id.parent_id.id)])
                if address:
                    rec.street = address.street
                    rec.street2 = address.street2
                    rec.zip = address.zip
                    rec.city = address.city
                    rec.state_id = address.state_id
                    rec.country_id = address.country_id
                    rec._get_json_address()

    @api.model
    def default_get(self, fields):
        """Set default values for partner addresses."""
        res = super(ResPartnerAddress, self).default_get(fields)

        # set default country for addresses, it won't work with the normal
        # default handling because of the new address handling
        res['country_id'] = self.env.ref('base.de').id

        return res

    @api.model
    def create(self, vals):
        """Update preferred address for related partner in addition."""
        if vals.get('preferred', False) and vals.get('partner_id', False):
            self.clean_preferred_addresses(vals['partner_id'])

        rec = super(ResPartnerAddress, self).create(vals)
        if rec.preferred:
            rec.set_partner_preferred_address(rec.partner_id)

        return rec

    @api.multi
    def write(self, vals):
        """Update preferred address for related partner in addition."""
        if vals.get('preferred', False):
            for rec in self:
                self.clean_preferred_addresses(rec.partner_id.id)
        res = super(ResPartnerAddress, self).write(vals)
        for rec in self:
            if rec.preferred:
                rec.set_partner_preferred_address(rec.partner_id)

        return res

    @api.multi
    def unlink(self):
        """In addition clean preferred address data in partner."""
        update_partner_address = []
        for rec in self:
            update_partner_address.append(rec.partner_id)
        res = super(ResPartnerAddress, self).unlink()

        for partner in update_partner_address:
            if len(partner.child_address_ids) == 0:
                partner.write({
                    'preferred_address': False,
                })

        return res

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
        """Copy from account.invoice."""
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

    def clean_preferred_addresses(self, partner_id):
        """Set preferred flag for all partner addresses to false."""
        addresses = self.search(
            [('preferred', '=', True),
             ('partner_id', '=', partner_id)])
        if addresses:
            addresses.write({'preferred': False})

        return True

    def set_partner_preferred_address(self, partner):
        """Set preferred address for given partner."""
        partner.write({
            'preferred_address': self.id,
        })

        return True

    @api.multi
    def open_address(self):
        """Open the partner address modal in partner detail views."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Address'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self[0].id,
            'target': 'current',
        }

    @api.multi
    def address_parent(self):
        """The Id of the parent."""
        if self.partner_id:
            return self.partner_id.id
        return False

    def _address_fields(self, cr, uid, context=None):
        """Adapt from openerp/addons/base/res/res_partner.py.

        Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set.
        """
        return list(ADDRESS_FIELDS)

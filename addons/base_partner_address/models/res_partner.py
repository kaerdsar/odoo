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

ADDRESS_TYPES = [
    ('private', 'Private'),
    ('business', 'Business'),
    ('other', 'Other'),
]


class ResPartner(models.Model):

    """Partner updates like new address handling, default values etc."""

    _inherit = 'res.partner'

    website = fields.Char('Website', size=128,
                          help="Website of Partner or Company")
    type = fields.Selection(
        [('default', 'Default'), ('invoice', 'Invoice'),
         ('delivery', 'Shipping'), ('contact', 'Contact'), ('other', 'Other'),
         ('address', 'Address')], 'Address Type',
        help="Used to select automatically the right address according to the"
             "context in sales and purchases documents.")
    
    preferred_address = fields.Many2one('res.partner.address', 'Preferred Address')
    partner_address_ids = fields.One2many('res.partner.address', 'partner_id',
                                          'Addresses')
    
    preferred_email = fields.Many2one('res.partner.email', 'Preferred Email')
    partner_email_ids = fields.One2many('res.partner.email', 'partner_id',
                                        'Email Addresses')
    
    partner_phone_ids = fields.One2many('res.partner.phone', 'partner_id',
                                        'Phones')

    @api.model
    def get_address(self, addr_type, first=False):
        """Return address of type addr_type or first address."""
        rpa_obj = self.env['res.partner.address']
        # it is possible that self._uid is None, especially after a server
        # restart, we would get an error like "AccessError: ('No value found
        # for res.partner(21,).partner_address_ids', None)" without sudo()
        address = rpa_obj.sudo().search(
            [('partner_id', '=', self.id), ('type', '=', addr_type)],
            order='id ASC', limit=1)
        if address:
            return address

        if first:
            address = rpa_obj.sudo().search([('partner_id', '=', self.id)],
                                            order='id ASC', limit=1)
            if address:
                return address

        return False

    @api.model
    def get_phone(self, phone_type):
        """Return first phone number of type phone_type."""
        domain = [('partner_id', '=', self.id)]
        if phone_type:
            domain.append(('type', '=', phone_type))
        # it is possible that self._uid is None, especially after a server
        # restart, we would get an error like "AccessError: ('No value found
        # for res.partner(21,).partner_address_ids', None)" without sudo()
        phone = self.env['res.partner.phone'].sudo().search(
            domain, order='id ASC', limit=1)

        return phone or False

    @api.onchange('name')
    def name_change(self):
        """Set parent_id forwarded from partner_shipping_id in sale orders."""
        if not self.parent_id and self._context.get('parent_id', False):
            self.parent_id = self._context['parent_id']

    @api.model
    def default_get(self, fields):
        """Set default values for company partners and partner addresses."""
        res = super(ResPartner, self).default_get(fields)

        # we don't want a default name for company contacts
        if self._context.get('is_company', False):
            res['name'] = ''

        return res

    @api.model
    def _handle_first_contact_creation(self, partner):
        """Skip function to avoid a problem when creating partners.

        Problem: If you create a partner in contacts (not in sale or purchase
        section) and assign one address the partner is flagged as company. It
        also fixes a problem when you create more than one address at a time.

        Original function description: On creation of first contact for a
        company (or root) that has no address, assume contact address was meant
        to be company address.
        """
        pass

    @api.model
    def create(self, vals):
        """Overwrite module: base.

        Adds computed partner sequence to partner (only for company partners).
        Set address flag if needed.
        """
        if vals.get('is_company', False):
            vals['ref'] = self.env['ir.sequence'].\
                next_by_code('res.partner') or '-'
        if not vals.get('lang', False):
            vals['lang'] = 'de_DE'

        rec = super(ResPartner, self).create(vals)

        return rec

    @api.model
    def unlink(self):
        """Remove all contact information if partner will be removed."""
        for partner in self:
            if partner.partner_address_ids:
                partner.partner_address_ids.unlink()
            if partner.partner_email_ids:
                partner.partner_email_ids.unlink()
            if partner.partner_phone_ids:
                partner.partner_phone_ids.unlink()
        return super(ResPartner, self).unlink()

    @api.multi
    def name_get(self):
        """
        Overwrite module: base.

        Add address type to address name labels.
        """
        res = []
        for record in self:
            name = record.name
            if record.parent_id and not record.is_company:
                if self._context.get('show_email', False) or \
                        self._context.get('lr_sale_order_view', False) and \
                        not self._context.get('future_display_name', False):
                    name = name
                else:
                    name = "%s, %s" % (record.parent_id.name, name)
            if self._context.get('show_address'):
                name = name + "\n" + self._display_address(
                    record, without_company=True)
                name = name.replace('\n\n', '\n')
                name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and record.email:
                email = record.email
                name = "%s <%s>" % (name, email)
            res.append((record.id, name))
        return res

    @api.model
    def _display_address(self, partner, without_company=False):
        """Overwrite module: base.

        Changed address line order, zip before city and excluding of
        state_code.
        """
        # get the information that will be injected into the display format
        # get the address format

        addr = partner.preferred_address
        if addr:
            address_format = addr.country_id and \
                addr.country_id.address_format or \
                "%(street)s\n%(street2)s\n%(zip)s %(city)s\n%(country_name)s"

            company_name = ''
            if addr.partner_id.is_company:
                company_name = addr.partner_id.name
            elif addr.partner_id.parent_id and \
                    addr.partner_id.parent_id.is_company:
                company_name = addr.partner_id.parent_id.name

            args = {
                'state_code': addr.state_id and addr.state_id.code or '',
                'state_name': addr.state_id and addr.state_id.name or '',
                'country_code': addr.country_id and addr.country_id.code or '',
                'country_name': addr.country_id and addr.country_id.name or '',
                'company_name': company_name,
            }
            for field in addr._address_fields():
                args[field] = getattr(addr, field) or ''
            if without_company:
                args['company_name'] = ''
            elif addr.partner_id.is_company or \
                    (addr.partner_id.parent_id and
                     addr.partner_id.parent_id.is_company):
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

        return ''

    @api.constrains('partner_address_ids')
    def _check_partner_address(self):
        """Check if partner contact has at least one address.

        In addition check if partner has exactly one address ticked as
        preferred address.
        """
        if not self.partner_address_ids:
            raise ValidationError(
                _('You cannot create a contact without an address.'))

        addresses = self.env['res.partner.address'].search(
            [('partner_id', '=', self.id), ('preferred', '=', True)])

        if len(addresses) != 1:
            raise ValidationError(
                _('You have to tick exact one address as preferred '
                  'address.'))

    @api.constrains('partner_email_ids')
    def _check_partner_email_address(self):
        """Check for preferred email address in partner contact.

        The check should only be done if there is at least one email address.
        Means email addresses are not required for a partner contract.
        """
        preferred_emails = 0
        for email in self.partner_email_ids:
            if email.preferred:
                preferred_emails += 1
        if len(self.partner_email_ids) > 0 and preferred_emails != 1:
            raise ValidationError(
                _('You have to tick exact one email address as preferred email'
                  ' address.'))

    @api.multi
    def address_get_all(self, adr_pref=None):
        """Copy of address_get function embrace the new address handling.

        Because we don't know how big are the impacts of this changings we
        copied the function and didn't overwrite this. This custom function is
        used in onchange_partner_id of sale.py.
        """
        adr_pref = set(adr_pref or [])
        if 'default' not in adr_pref:
            adr_pref.add('default')
        result = {}
        for partner in self:
            for adr_type in adr_pref:
                result[adr_type] = partner.id
            return result
        return result

    def set_preferred_email(self, email_address, email_type=False):
        """Set preferred email of current partner.

        If a record with email already exists this record will be marked as
        preferred email. If no record with email exists a new record will be
        created and marked as preferred email.
        """
        param_email_type = email_type
        if not email_type:
            email_type = 'private'

        rpe_obj = self.env['res.partner.email']
        emails = rpe_obj.search([('preferred', '=', True),
                                 ('partner_id', '=', self.id)])
        if emails:
            emails.write({'preferred': False})

        email = rpe_obj.search([('name', '=', email_address)], limit=1)
        if email:
            values = {'preferred': True}
            if param_email_type:
                values.update({'type': param_email_type})
            email.write(values)
        else:
            email = rpe_obj.create({
                'name': email_address,
                'partner_id': self.id,
                'type': email_type,
                'preferred': True,
            })
        return email

    def get_preferred_email_label(self):
        """Return preferred email type label."""
        email = self.preferred_email
        if email and email.type:
            return dict(email.fields_get(allfields=['type'])
                        ['type']['selection'])[email.type]
        return False

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        """ Search for address fields in contact information related to res.partner.address,
         res.partner.email and res.partner.phone instead of the fields int the current model. """
        address_fields = ['street', 'street2', 'zip', 'city']
        phone_fields = ['phone', 'fax', 'mobile']
        for arg in args:
            if isinstance(arg, list) and arg[0] in address_fields:
                arg[0] = 'preferred_address.%s' % arg[0]
            elif isinstance(arg, list) and arg[0] == 'email':
                arg[0] = 'preferred_email.name'
            elif isinstance(arg, list) and arg[0] in phone_fields:
                arg[0] = 'partner_phone_ids.name'
        return super(ResPartner, self).search(cr, user, args, offset=offset, limit=limit,
                                              order=order, context=context, count=count)

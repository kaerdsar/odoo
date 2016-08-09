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
import openerp.tests.common


class TestPartner(openerp.tests.common.TransactionCase):
    at_install = False
    post_install = True

    def test_01_partner_address(self):
        """----- Test if business address is company address."""
        res_partner = self.env['res.partner']
        res_partner_address = self.env['res.partner.address']

        company = res_partner.create({
            'name': 'Company',
            'is_company': True,
        })
        res_partner_address.create({
            'partner_id': company.id,
            'type': 'business',
            'city': 'Test Company',
        })
        customer = res_partner.create({
            'name': 'customer',
            'parent_id': company.id,
        })
        address = res_partner_address.create({
            'partner_id': customer.id,
            'type': 'business',
        })
        address.onchange_type()
        self.assertEqual(address.city, 'Test Company')

    def test_02_search_contact_fields(self):
        """----- Test if contact fields searches in the
        res.partner.address, res.partner.phone and res.partner.email
        related models """
        res_partner = self.env['res.partner']

        # Create company
        res_partner.create({
            'name': 'Company',
            'is_company': True,
            'child_address_ids': [(0, 0, {
                'type': 'business',
                'street': 'Test Street',
                'zip': 10500,
                'city': 'Test City',
                'preferred': True
            })],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'Info@company.com',
                'preferred': True
            })],
            'partner_phone_ids': [
                (0, 0, {
                    'type': 'phone',
                    'name': 12345
                }),
                (0, 0, {
                    'type': 'mobile',
                    'name': 678911
                }),
                (0, 0, {
                    'type': 'fax',
                    'name': 333777
                })
            ]
        })

        # Search street
        partners = res_partner.search([['street', '=', 'Test Street']])
        self.assertEqual(partners[0].preferred_address.street, 'Test Street')

        # Search zip
        partners = res_partner.search([['zip', '=', '10500']])
        self.assertEqual(partners[0].preferred_address.zip, '10500')

        # Search city
        partners = res_partner.search([['city', '=', 'Test City']])
        self.assertEqual(partners[0].preferred_address.city, 'Test City')

        # Search email and check correct lower
        partners = res_partner.search([['email', '=', 'info@company.com']])
        self.assertEqual(partners[0].preferred_email.name, 'info@company.com')

        # Search phone
        partners = res_partner.search([['phone', '=', '12345']])
        self.assertIn('12345', [x.name for x in partners[0].partner_phone_ids])

        # Search mobile
        partners = res_partner.search([['mobile', '=', '678911']])
        self.assertIn('678911', [x.name
                                 for x in partners[0].partner_phone_ids])

        # Search fax
        partners = res_partner.search([['fax', '=', '333777']])
        self.assertIn('333777', [x.name
                                 for x in partners[0].partner_phone_ids])

    def test_03_merge_partners_with_addresses_case_1(self):
        """Test case 1.

        Contact A has private address "F"
        Contact B has private address "M" AND business address "M"
        --> Merge both Contacts into Contact A
        --> Merged Contact has private address "F" AND business address "M"
        """
        res_partner = self.env['res.partner']
        partner_merge_1 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [(0, 0, {
                'type': 'private',
                'city': 'Private City 1',
                'preferred': True
            })],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge1@lr-partner.com',
                'preferred': True
            })]
        })
        partner_merge_2 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [
                (0, 0, {
                    'type': 'private',
                    'city': 'Private City 2',
                    'preferred': False
                }),
                (0, 0, {
                    'type': 'business',
                    'city': 'Business City 2',
                    'preferred': True
                })
            ],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge2@lr-partner.com',
                'preferred': True
            })],
            'partner_phone_ids': [
                (0, 0, {'type': 'phone', 'name': 12345}),
            ]
        })

        merge_ids = partner_merge_1.id, partner_merge_2.id
        merge_wizard = self.env['base.partner.merge.automatic.wizard'].create({
            'partner_ids': [(6, False, merge_ids)],
            'dst_partner_id': partner_merge_1.id
        })

        merge_wizard.merge_cb()

        partner = res_partner.search([('id', 'in', merge_ids)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.id, partner_merge_1.id)
        self.assertEqual(len(partner.partner_email_ids), 1)
        self.assertEqual(len(partner.child_address_ids), 2)
        self.assertEqual(len(partner.partner_phone_ids), 0)
        for a in partner.child_address_ids:
            if a.type == 'private':
                self.assertEqual(a.city, 'Private City 1')
                self.assertTrue(a.preferred)
            if a.type == 'business':
                self.assertEqual(a.city, 'Business City 2')
                self.assertFalse(a.preferred)

    def test_03_merge_partners_with_addresses_case_2(self):
        """Test case 2.

        Contact A has business address "F"
        Contact B has private address "M" AND business address "M"
        --> Merge both Contacts into Contact A
        --> Merged Contact has private address "M" AND business address "F"
        """
        res_partner = self.env['res.partner']
        partner_merge_1 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [(0, 0, {
                'type': 'business',
                'city': 'Business City 1',
                'preferred': True
            })],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge1@lr-partner.com',
                'preferred': True
            })]
        })
        partner_merge_2 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [
                (0, 0, {
                    'type': 'private',
                    'city': 'Private City 2',
                    'preferred': True
                }),
                (0, 0, {
                    'type': 'business',
                    'city': 'Business City 2',
                    'preferred': False
                })
            ],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge2@lr-partner.com',
                'preferred': True
            })]
        })

        merge_ids = partner_merge_1.id, partner_merge_2.id
        merge_wizard = self.env['base.partner.merge.automatic.wizard'].create({
            'partner_ids': [(6, False, merge_ids)],
            'dst_partner_id': partner_merge_1.id
        })

        merge_wizard.merge_cb()

        partner = res_partner.search([('id', 'in', merge_ids)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.id, partner_merge_1.id)
        self.assertEqual(len(partner.partner_email_ids), 1)
        self.assertEqual(len(partner.child_address_ids), 2)
        for a in partner.child_address_ids:
            if a.type == 'private':
                self.assertEqual(a.city, 'Private City 2')
                self.assertFalse(a.preferred)
            if a.type == 'business':
                self.assertEqual(a.city, 'Business City 1')
                self.assertTrue(a.preferred)

    def test_03_merge_partners_with_addresses_case_3(self):
        """Test case 3.

        Contact A has private address "F" AND business address "F"
        Contact B has private address "M" AND business address "M"
        --> Merge both Contacts into Contact A
        --> Merged Contact has private address "F" AND business address "F"
        """
        res_partner = self.env['res.partner']
        partner_merge_1 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [
                (0, 0, {
                    'type': 'private',
                    'city': 'Private City 1',
                    'preferred': True
                }),
                (0, 0, {
                    'type': 'business',
                    'city': 'Business City 1',
                    'preferred': False
                })
            ],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge1@lr-partner.com',
                'preferred': True
            })]
        })
        partner_merge_2 = res_partner.create({
            'name': 'Partner Merge 1',
            'child_address_ids': [
                (0, 0, {
                    'type': 'private',
                    'city': 'Private City 2',
                    'preferred': False
                }),
                (0, 0, {
                    'type': 'business',
                    'city': 'Business City 2',
                    'preferred': True
                })
            ],
            'partner_email_ids': [(0, 0, {
                'type': 'business',
                'name': 'merge2@lr-partner.com',
                'preferred': True
            })]
        })

        merge_ids = partner_merge_1.id, partner_merge_2.id
        merge_wizard = self.env['base.partner.merge.automatic.wizard'].create({
            'partner_ids': [(6, False, merge_ids)],
            'dst_partner_id': partner_merge_1.id
        })

        merge_wizard.merge_cb()

        partner = res_partner.search([('id', 'in', merge_ids)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.id, partner_merge_1.id)
        self.assertEqual(len(partner.partner_email_ids), 1)
        self.assertEqual(len(partner.child_address_ids), 2)
        for a in partner.child_address_ids:
            if a.type == 'private':
                self.assertEqual(a.city, 'Private City 1')
                self.assertTrue(a.preferred)
            if a.type == 'business':
                self.assertEqual(a.city, 'Business City 1')
                self.assertFalse(a.preferred)

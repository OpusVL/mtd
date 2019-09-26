# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class VatCalculation(models.Model):
    _name = 'mtd_vat.vat_calculation'

    def retrieve_account_move_lines_for_vat_calculation(self, company, date_from, date_to,
                                                        date_vat_period, vat_posted):

        if date_from >= date_to:
            raise exceptions.Warning("Period start date is greater than period end date.\n " +
                                     "Please check the obligation date with HMRC posting date.")

        sale_purchase_tax_code = self.env['account.tax'].search([])

        for record in sale_purchase_tax_code:
            self.calculate_originator_taxcode_balance(record, date_from, date_to,
                                                      company.id, date_vat_period, vat_posted)
            self.calculate_taxes_taxcode_balance(record, date_from, date_to,
                                                 company.id, date_vat_period, vat_posted)

        # work out the 9 VAT boxes
        calculation_table = self.env['mtd_vat.vat_calculation_table'].search([('date_from', '=', date_from),
                                                                              ('date_to', '=', date_to),
                                                                              ('company_id', '=', company.id)])

        # box 1 calculations
        box1_tag_list = ['ST11', 'ST1']
        box1_calculation_rows = self.retrieve_calculation_rows(calculation_table, box1_tag_list)
        box1_vat = self.retrieve_sum_value_for_originator_tax(box1_calculation_rows)

        # box 2 calculations
        box2_tag_list = ['PT8M']
        box2_calculation_rows = self.retrieve_calculation_rows(calculation_table, box2_tag_list)
        box2_vat = self.retrieve_sum_value_for_originator_tax(box2_calculation_rows)

        # box 3 calculation
        box3_vat = (box1_vat + box2_vat)

        # box 4 calculations
        box4_tag_list = ['PT11', 'PT5', 'PT1', 'PT8R']
        box4_calculation_rows = self.retrieve_calculation_rows(calculation_table, box4_tag_list)
        box4_vat = self.retrieve_sum_value_for_originator_tax(box4_calculation_rows)

        # box5 calculations
        box5_vat = (box3_vat - box4_vat)

        # box6 calculations
        box6_tag_list = ['ST11', 'ST2', 'ST1', 'ST0', 'ST4']
        box6_calculation_rows = self.retrieve_calculation_rows(calculation_table, box6_tag_list)
        box6_vat = self.retrieve_sum_value_for_taxes(box6_calculation_rows)

        # box7 calculations
        box7_tag_list = ['PT11', 'PT5', 'PT2', 'PT1', 'PT0', 'PT7', 'PT8']
        box7_calculation_rows = self.retrieve_calculation_rows(calculation_table, box7_tag_list)
        box7_vat = self.retrieve_sum_value_for_taxes(box7_calculation_rows)

        # box8 calculations
        box8_tag_list = ['ST4']
        box8_calculation_rows = self.retrieve_calculation_rows(calculation_table, box8_tag_list)
        box8_vat = self.retrieve_sum_value_for_taxes(box8_calculation_rows)

        # box9 calculations
        box9_tag_list = ['PT7', 'PT8']
        box9_calculation_rows = self.retrieve_calculation_rows(calculation_table, box9_tag_list)
        box9_vat = self.retrieve_sum_value_for_taxes(box9_calculation_rows)

        return box1_vat, box2_vat, box3_vat, box4_vat, box5_vat, box6_vat, box7_vat, box8_vat, box9_vat

    def retrieve_calculation_rows(self, calculation_table, tag_list):
        calculation_rows = calculation_table.with_context(tag_list=tag_list).filtered(
            lambda calculation_rec: calculation_rec.tag_id in calculation_rec._context['tag_list']
        )
        return calculation_rows

    # vat boxs(1, 2, 4)
    def retrieve_sum_value_for_originator_tax(self, calculation_rows):
        balance = []

        for rec in calculation_rows:
            if not rec.taxes:
                balance.append(rec.balance)

        sum_value = sum(balance)
        return sum_value

    # vat boxes(6, 7, 8, 9)
    def retrieve_sum_value_for_taxes(self, calculation_rows):
        balance = []
        for rec in calculation_rows:
            if not rec.name:
                balance.append(rec.balance)

        sum_value = sum(balance)
        return sum_value

    def calculate_originator_taxcode_balance(self, tax_code_record, date_from, date_to,
                                             company_id, date_vat_period, vat_posted):
        tax_tag_name = tax_code_record.tag_ids.name
        uk_tax_scope = tax_code_record.vat_tax_scope

        move_lines_for_tax = self.env['account.move.line'].search([
            ('company_id', '=', company_id),
            ('date', '>=', date_vat_period),
            ('date', '<=', date_to),
            ('vat', '=', vat_posted),
            ('tax_line_id.id', '=', tax_code_record.id)])

        line_ids = []
        credit = []
        debit = []
        for record in move_lines_for_tax:

            line_ids.append(record.id)
            credit.append(record.credit)
            debit.append(record.debit)
            record.write({'date_vat_period': date_vat_period})

        sum_debit = sum(debit)
        sum_credit = sum(credit)
        balance = 0
        if uk_tax_scope in ['ST', 'PTR']:
            balance = (sum_credit - sum_debit)
        else:
            balance = (sum_debit - sum_credit)

        if move_lines_for_tax:
            self.create_vat_calculation_record(
                tax_code_record.name,
                None,
                sum_debit,
                sum_credit,
                balance,
                tax_tag_name,
                line_ids,
                date_from,
                date_to,
                company_id,
                date_vat_period)

    def calculate_taxes_taxcode_balance(self, tax_code_record, date_from, date_to,
                                        company_id, date_vat_period, vat_posted):
        tax_tag_name = tax_code_record.tag_ids.name
        uk_tax_scope = tax_code_record.vat_tax_scope

        move_lines_for_tax = self.env['account.move.line'].search([
            ('company_id', '=', company_id),
            ('date', '>=', date_vat_period),
            ('date', '<=', date_to),
            ('vat', '=', vat_posted),
            ('tax_ids.id', '=', tax_code_record.id)])

        line_ids = []
        credit = []
        debit = []
        for record in move_lines_for_tax:
            line_ids.append(record.id)
            credit.append(record.credit)
            debit.append(record.debit)
            record.write({'date_vat_period': date_vat_period})

        sum_debit = sum(debit)
        sum_credit = sum(credit)
        balance = 0
        if uk_tax_scope in ['ST', 'PTR']:
            balance = (sum_credit - sum_debit)
        else:
            balance = (sum_debit - sum_credit)

        if move_lines_for_tax:
            self.create_vat_calculation_record(
                None,
                tax_code_record.name,
                sum_debit,
                sum_credit,
                balance,
                tax_tag_name,
                line_ids,
                date_from,
                date_to,
                company_id,
                date_vat_period)

    def create_vat_calculation_record(self, originator_name, taxes_name, sum_debit, sum_credit, balance,
                                      tag_id, line_ids, date_from, date_to, company_id, date_vat_period):

        calculation_table_obj = self.env['mtd_vat.vat_calculation_table'].search([('date_from', '=', date_from),
                                                                                  ('date_to', '=', date_to),
                                                                                  ('tag_id', '=', tag_id),
                                                                                  ('name', '=', originator_name),
                                                                                  ('taxes', '=', taxes_name),
                                                                                  ('company_id', '=', company_id)])
        if not calculation_table_obj:

            calculation_table = calculation_table_obj.create({
                'name': originator_name,
                'taxes': taxes_name,
                'sum_debit': sum_debit,
                'sum_credit': sum_credit,
                'balance': balance,
                'tag_id': tag_id,
                'move_line_ids': line_ids,
                'date_from': date_from,
                'date_to': date_to,
                'company_id': company_id,
                'date_vat_period': date_vat_period,
            })
        else:
            calculation_table_obj.name = originator_name
            calculation_table_obj.taxes = taxes_name
            calculation_table_obj.sum_debit = sum_debit
            calculation_table_obj.sum_credit = sum_credit
            calculation_table_obj.balance = balance
            calculation_table_obj.tag_id = tag_id
            calculation_table_obj.move_line_ids = line_ids
            calculation_table_obj.date_from = date_from
            calculation_table_obj.date_to = date_to
            calculation_table_obj.company_id = company_id
            calculation_table_obj.date_vat_period = date_vat_period


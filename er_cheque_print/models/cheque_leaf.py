# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError


class ChequeLeaf(models.Model):
    _name = 'cheque.leaf'
    _description = 'Cheque Leaf'
    _order = 'number'
    _rec_name = 'number'

    cheque_book_id = fields.Many2one('cheque.book', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='cheque_book_id.company_id', store=True)
    number = fields.Char(required=True)

    state = fields.Selection([
        ('unused', 'Unused'),
        ('used', 'Used'),
        ('voided', 'Voided'),
        ('cancelled', 'Cancelled'),
    ], default='unused', required=True)

    payment_id = fields.Many2one('account.payment', string="Payment", readonly=True, copy=False)

    # Snapshot fields are frozen at print time, independent of later edits
    # to the related payment, so printed-cheque history never silently
    # changes underneath you.
    payee_name_snapshot = fields.Char(string="Payee Name", readonly=True)
    amount_snapshot = fields.Monetary(string="Amount", readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    date_snapshot = fields.Date(string="Date", readonly=True)
    amount_words_snapshot = fields.Char(string="Amount in Words", readonly=True)

    # Extended snapshot fields written by the print wizard
    memo_snapshot = fields.Char(string="Memo", readonly=True)
    is_ac_payable_snapshot = fields.Boolean(string="A/C Payee", readonly=True)
    bank_name = fields.Char(string="Bank Name", readonly=True)
    bank_account_number = fields.Char(string="Bank Account Number", readonly=True)
    bank_email = fields.Char(string="Bank Email", readonly=True)
    bank_address = fields.Char(string="Bank Address", readonly=True)

    printed_date = fields.Datetime(readonly=True)
    void_reason = fields.Char()

    _sql_constraints = [
        ('uniq_number_per_book', 'unique(cheque_book_id, number)',
         'Cheque numbers must be unique within a cheque book.'),
    ]

    def _split_payee_name(self, max_lines=3, max_chars=15):
        """Split payee_name_snapshot across up to *max_lines* lines.

        Every line — including the last — is filled by whole-word boundaries so
        that no word is ever cut mid-string by the line-filling pass.  When
        words still remain after all lines are consumed the last line is
        post-processed: trailing whole words are removed until the remaining
        text plus the literal suffix "..." fits within *max_chars*.  A
        mid-word hard-truncation is used only as a last resort when even a
        single word cannot coexist with "..." inside *max_chars*.

        Args:
            max_lines (int): Number of output lines (default 3).
            max_chars (int): Maximum characters per line (default 15).

        Returns:
            list[str]: Exactly *max_lines* strings (empty strings for unused
                       lines).
        """
        self.ensure_one()
        words = (self.payee_name_snapshot or '').split()
        if max_lines <= 0:
            return []

        lines = [''] * max_lines
        if not words:
            return lines

        index = 0  # next word to place

        for line_idx in range(max_lines):
            if index >= len(words):
                break  # all words placed; remaining lines stay ''

            # ── Fill this line by whole-word boundary ────────────────────────
            current = ''
            while index < len(words):
                next_word = words[index]
                candidate = next_word if not current else f'{current} {next_word}'

                if len(candidate) > max_chars:
                    # The next word won't fit.  If the line is still empty it
                    # means a single word is already wider than max_chars —
                    # hard-truncate it (last-resort) and advance.
                    if not current:
                        if max_chars <= 3:
                            current = next_word[:max_chars]
                        else:
                            current = next_word[:max_chars - 3] + '...'
                        index += 1
                    break  # stop adding words to this line

                current = candidate
                index += 1

            lines[line_idx] = current

        # ── Post-process last non-empty line if words remain unplaced ────────
        if index < len(words):
            # Remaining words that didn't fit get appended conceptually; we
            # need to trim the last filled line to make room for "...".
            last_idx = max_lines - 1
            # Reconstruct what *would* be on the last line plus the overflow.
            overflow_words = lines[last_idx].split() + words[index:]
            candidate_words = list(overflow_words)

            placed = False
            while len(candidate_words) > 1:
                candidate = ' '.join(candidate_words[:-1]) + '...'
                if len(candidate) <= max_chars:
                    lines[last_idx] = candidate
                    placed = True
                    break
                candidate_words.pop()

            if not placed:
                # Only one word left — try word + "..."
                word = candidate_words[0] if candidate_words else ''
                if len(word) + 3 <= max_chars:
                    lines[last_idx] = word + '...'
                else:
                    # True last resort: hard-slice the single word
                    if max_chars <= 3:
                        lines[last_idx] = word[:max_chars]
                    else:
                        lines[last_idx] = word[:max_chars - 3] + '...'

        return lines

    def action_void(self):
        for rec in self:
            if not rec.void_reason:
                raise ValidationError("Please provide a Void Reason before voiding the cheque.")
            # Allow voiding cheques in any state (including 'used')
            # if rec.state == 'used':
            #     raise ValidationError(
            #         "A used cheque leaf cannot be voided directly; "
            #         "cancel or reverse the related payment instead.")
            rec.state = 'voided'

    def action_reset_to_unused(self):
        for rec in self:
            rec.write({
                'state': 'unused',
                'payment_id': False,
                'payee_name_snapshot': False,
                'amount_snapshot': 0.0,
                'date_snapshot': False,
                'amount_words_snapshot': False,
                'printed_date': False,
            })

    def mark_used(self, payment, payee_name, amount, currency, date, amount_words):
        self.ensure_one()
        if self.state != 'unused':
            raise ValidationError(
                f"Cheque leaf {self.number} is not available (current state: {self.state}).")
        self.write({
            'state': 'used',
            'payment_id': payment.id if payment else False,
            'payee_name_snapshot': payee_name,
            'amount_snapshot': amount,
            'currency_id': currency.id if currency else False,
            'date_snapshot': date,
            'amount_words_snapshot': amount_words,
            'printed_date': fields.Datetime.now(),
        })
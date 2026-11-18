from odoo import models, fields, api
from odoo.exceptions import UserError

class HotelPaymentWizard(models.TransientModel):
    _name = 'hotel.payment.wizard'
    _description = 'Register Hotel Payment'

    booking_id = fields.Many2one('hotel.booking', string='Booking', required=True)
    guest_name = fields.Char(related='booking_id.guest_name', readonly=True)
    booking_total = fields.Monetary(related='booking_id.total_amount', readonly=True)
    amount_paid = fields.Monetary(related='booking_id.amount_paid', readonly=True)
    balance = fields.Monetary(related='booking_id.balance', readonly=True)
    
    payment_date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one(related='booking_id.currency_id', readonly=True)
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('mtn', 'MTN Mobile Money'),
        ('telecel', 'Telecel Cash'),
        ('airteltigo', 'AirtelTigo Money'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('other', 'Other'),
    ], string='Payment Method', required=True, default='cash')
    
    reference_number = fields.Char('Reference Number', help='Transaction ID, Receipt Number, etc.')
    notes = fields.Text('Notes')
    
    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise UserError('Payment amount must be greater than zero!')
            
            if wizard.amount > wizard.balance:
                raise UserError(
                    f'Payment amount (GHS {wizard.amount:.2f}) cannot exceed '
                    f'remaining balance (GHS {wizard.balance:.2f})!'
                )
    
    def action_register_payment(self):
        """Create payment record and close wizard"""
        self.ensure_one()
        
        # Create payment
        payment = self.env['hotel.payment'].create({
            'booking_id': self.booking_id.id,
            'payment_date': self.payment_date,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
        })
        
        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Payment Registered!',
                'message': f'Payment of GHS {self.amount:.2f} recorded successfully. '
                          f'Remaining balance: GHS {self.booking_id.balance:.2f}',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelPayment(models.Model):
    _name = 'hotel.payment'
    _description = 'Hotel Booking Payment'
    _order = 'payment_date desc, id desc'

    name = fields.Char('Payment Reference', required=True, copy=False, readonly=True,
                      default=lambda self: 'New')
    
    booking_id = fields.Many2one('hotel.booking', string='Booking', required=True, ondelete='cascade')
    guest_name = fields.Char(related='booking_id.guest_name', string='Guest Name', readonly=True)
    
    payment_date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
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
    
    # Computed fields
    booking_total = fields.Monetary(related='booking_id.total_amount', string='Booking Total', readonly=True)
    booking_balance = fields.Monetary(related='booking_id.balance', string='Remaining Balance', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.payment') or 'New'
        
        payments = super().create(vals_list)
        
        # Update booking's amount_paid
        for payment in payments:
            payment.booking_id._update_amount_paid()
        
        return payments
    
    def unlink(self):
        bookings = self.mapped('booking_id')
        result = super().unlink()
        # Update booking's amount_paid after deletion
        for booking in bookings:
            booking._update_amount_paid()
        return result
    
    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError('Payment amount must be greater than zero!')
            
            # Check if payment exceeds booking total
            total_paid = sum(payment.booking_id.payment_ids.mapped('amount'))
            if total_paid > payment.booking_id.total_amount:
                raise ValidationError(
                    f'Total payments (GHS {total_paid:.2f}) cannot exceed '
                    f'booking total (GHS {payment.booking_id.total_amount:.2f})!'
                )
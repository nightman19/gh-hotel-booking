from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Hotel Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'checkin_date desc, id desc'

    name = fields.Char('Booking Reference', required=True, copy=False, readonly=True,
                      default=lambda self: 'New')

    # Guest Information
    guest_name = fields.Char('Guest Name', required=True, tracking=True)
    guest_phone = fields.Char('Phone Number', required=True, tracking=True)
    guest_email = fields.Char('Email')
    guest_id_number = fields.Char('ID/Passport Number')
    number_of_guests = fields.Integer('Number of Guests', default=1, required=True)

    # Booking Details
    room_id = fields.Many2one('hotel.room', string='Room', required=True, tracking=True)
    room_type = fields.Selection(related='room_id.room_type', string='Room Type', readonly=True)

    checkin_date = fields.Date('Check-in Date', required=True, tracking=True)
    checkout_date = fields.Date('Check-out Date', required=True, tracking=True)

    number_of_nights = fields.Integer('Number of Nights', compute='_compute_nights', store=True)

    # Pricing
    rate_per_night = fields.Monetary('Rate per Night', currency_field='currency_id', required=True)
    total_amount = fields.Monetary('Total Amount', compute='_compute_total', store=True, currency_field='currency_id')
    amount_paid = fields.Monetary('Amount Paid', currency_field='currency_id', compute='_compute_amount_paid', store=True, tracking=True)
    balance = fields.Monetary('Balance', compute='_compute_balance', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # Payment tracking
    payment_ids = fields.One2many('hotel.payment', 'booking_id', string='Payments')
    payment_count = fields.Integer('Payment Count', compute='_compute_payment_count')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checkedin', 'Checked In'),
        ('checkedout', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ], string='Payment Status', compute='_compute_payment_status', store=True)

    # Additional Info
    special_requests = fields.Text('Special Requests')
    notes = fields.Text('Internal Notes')

    # Computed fields for calendar color
    color = fields.Integer('Color', compute='_compute_color')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.booking') or 'New'
        return super().create(vals_list)

    @api.depends('checkin_date', 'checkout_date')
    def _compute_nights(self):
        for booking in self:
            if booking.checkin_date and booking.checkout_date:
                delta = booking.checkout_date - booking.checkin_date
                booking.number_of_nights = delta.days if delta.days > 0 else 0
            else:
                booking.number_of_nights = 0

    @api.depends('number_of_nights', 'rate_per_night')
    def _compute_total(self):
        for booking in self:
            booking.total_amount = booking.number_of_nights * booking.rate_per_night

    @api.depends('payment_ids.amount')
    def _compute_amount_paid(self):
        for booking in self:
            booking.amount_paid = sum(booking.payment_ids.mapped('amount'))

    @api.depends('total_amount', 'amount_paid')
    def _compute_balance(self):
        for booking in self:
            booking.balance = booking.total_amount - booking.amount_paid

    @api.depends('balance')
    def _compute_payment_status(self):
        for booking in self:
            if booking.balance <= 0 and booking.total_amount > 0:
                booking.payment_status = 'paid'
            elif booking.amount_paid > 0:
                booking.payment_status = 'partial'
            else:
                booking.payment_status = 'unpaid'

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for booking in self:
            booking.payment_count = len(booking.payment_ids)

    @api.depends('state')
    def _compute_color(self):
        color_map = {
            'draft': 7,      # Gray
            'confirmed': 4,  # Blue
            'checkedin': 10, # Green
            'checkedout': 3, # Yellow
            'cancelled': 1,  # Red
        }
        for booking in self:
            booking.color = color_map.get(booking.state, 0)

    @api.onchange('room_id')
    def _onchange_room(self):
        if self.room_id:
            self.rate_per_night = self.room_id.rate_per_night

    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for booking in self:
            if booking.checkout_date <= booking.checkin_date:
                raise ValidationError('Check-out date must be after check-in date!')

    @api.constrains('room_id', 'checkin_date', 'checkout_date', 'state')
    def _check_room_availability(self):
        for booking in self:
            if booking.state in ['confirmed', 'checkedin'] and booking.room_id:
                overlapping = self.search([
                    ('id', '!=', booking.id),
                    ('room_id', '=', booking.room_id.id),
                    ('state', 'in', ['confirmed', 'checkedin']),
                    '|',
                    '&', ('checkin_date', '<=', booking.checkin_date),
                         ('checkout_date', '>', booking.checkin_date),
                    '&', ('checkin_date', '<', booking.checkout_date),
                         ('checkout_date', '>=', booking.checkout_date),
                ])
                if overlapping:
                    raise ValidationError(f'Room {booking.room_id.room_number} is already booked for these dates!')

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_checkin(self):
        self.write({'state': 'checkedin'})
        self.room_id.write({'status': 'occupied'})

    def action_checkout(self):
        self.write({'state': 'checkedout'})
        self.room_id.write({'status': 'cleaning'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    def action_register_payment(self):
        """Open payment wizard"""
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
                'default_amount': self.balance,
            }
        }

    def action_view_payments(self):
        """View all payments for this booking"""
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.payment',
            'view_mode': 'tree,form',
            'domain': [('booking_id', '=', self.id)],
            'context': {'default_booking_id': self.id}
        }

    def _update_amount_paid(self):
        """Update amount_paid when payments change"""
        self._compute_amount_paid()
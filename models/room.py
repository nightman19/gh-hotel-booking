from odoo import models, fields, api

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _order = 'room_number'
    
    name = fields.Char('Room Name', required=True, help='e.g., Standard Room 101')
    room_number = fields.Char('Room Number', required=True, help='e.g., 101, 201')
    
    room_type = fields.Selection([
        ('standard', 'Standard Room'),
        ('deluxe', 'Deluxe Room'),
        ('suite', 'Suite'),
        ('family', 'Family Room'),
    ], string='Room Type', required=True, default='standard')
    
    capacity = fields.Integer('Max Guests', default=2, help='Maximum number of guests')
    
    rate_per_night = fields.Monetary('Rate per Night', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('cleaning', 'Being Cleaned'),
    ], string='Status', default='available', required=True)
    
    floor = fields.Integer('Floor Number')
    
    amenities = fields.Text('Amenities', help='TV, AC, WiFi, etc.')
    notes = fields.Text('Notes')
    
    active = fields.Boolean('Active', default=True)
    
    # Statistics
    booking_count = fields.Integer('Total Bookings', compute='_compute_booking_count')
    
    @api.depends('room_number')
    def _compute_booking_count(self):
        for room in self:
            room.booking_count = self.env['hotel.booking'].search_count([
                ('room_id', '=', room.id)
            ])
    
    _room_number_unique = models.Constraint(
        'unique(room_number)', 'Room number must be unique!'
    )

from odoo import models, fields, api
from odoo.exceptions import UserError

class RoomBulkCreateWizard(models.TransientModel):
    _name = 'hotel.room.bulk.wizard'
    _description = 'Bulk Create Hotel Rooms'

    room_type = fields.Selection([
        ('standard', 'Standard Room'),
        ('deluxe', 'Deluxe Room'),
        ('suite', 'Suite'),
        ('family', 'Family Room'),
    ], string='Room Type', required=True, default='standard')

    quantity = fields.Integer(string='Number of Rooms', required=True, default=1)
    starting_number = fields.Integer(string='Starting Room Number', required=True, default=101)
    floor_number = fields.Integer(string='Floor Number', required=True, default=1)
    prefix = fields.Char(string='Room Prefix', help='Optional prefix for room names (e.g., "A", "B")')

    capacity = fields.Integer(string='Max Guests', required=True, default=2)
    rate_per_night = fields.Monetary(string='Rate per Night', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    amenities = fields.Text(string='Amenities', help='e.g., AC, TV, WiFi, Mini Bar')

    @api.onchange('room_type')
    def _onchange_room_type(self):
        """Auto-fill default values based on room type"""
        if self.room_type == 'standard':
            self.capacity = 2
            self.rate_per_night = 250.0
            self.amenities = 'AC, TV, WiFi'
        elif self.room_type == 'deluxe':
            self.capacity = 2
            self.rate_per_night = 400.0
            self.amenities = 'AC, TV, WiFi, Mini Bar, Balcony'
        elif self.room_type == 'suite':
            self.capacity = 3
            self.rate_per_night = 750.0
            self.amenities = 'AC, TV, WiFi, Mini Bar, Balcony, Jacuzzi, Living Room'
        elif self.room_type == 'family':
            self.capacity = 4
            self.rate_per_night = 500.0
            self.amenities = 'AC, TV, WiFi, Mini Bar, Extra Bed'

    def action_create_rooms(self):
        """Create multiple rooms based on wizard input"""
        self.ensure_one()

        if self.quantity <= 0:
            raise UserError("Number of rooms must be greater than 0")

        if self.quantity > 100:
            raise UserError("You can only create up to 100 rooms at once")

        Room = self.env['hotel.room']
        created_count = 0

        for i in range(self.quantity):
            room_number = self.starting_number + i

            # Build room number with optional prefix
            if self.prefix:
                room_number_str = f"{self.prefix}{room_number}"
            else:
                room_number_str = str(room_number)

            # Build room name
            room_type_name = dict(self._fields['room_type'].selection).get(self.room_type, 'Room')
            room_name = f"{room_type_name} {room_number_str}"

            # Check if room already exists
            existing_room = Room.search([('room_number', '=', room_number_str)], limit=1)
            if existing_room:
                raise UserError(f"Room {room_number_str} already exists. Please use a different starting number or prefix.")

            # Create the room
            room_vals = {
                'name': room_name,
                'room_number': room_number_str,
                'room_type': self.room_type,
                'capacity': self.capacity,
                'floor': self.floor_number,
                'rate_per_night': self.rate_per_night,
                'amenities': self.amenities,
                'active': True,
                'status': 'available',
            }

            Room.create(room_vals)
            created_count += 1

        # Return to rooms list view with success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': f'{created_count} room(s) created successfully!',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
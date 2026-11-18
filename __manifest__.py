{
    'name': 'Hotel/GuestHouse Booking',
    'version': '1.0.0',
    'category': 'Sales/Hotel',
    'summary': 'Hotel/Guesthouse booking management for Ghanaian hotels',
    'description': """
        Ghana Hotel Booking System
        ==========================
        Clean booking management for small hotels.

        Features:
        * Guest registration and management
        * Room booking with check-in/check-out dates
        * Room inventory management
        * Calendar view of bookings
        * Payment tracking
        * Guest history

        Built for simplicity - no complicated features, just what you need.
    """,
    'author': 'Umaru Nuru Mohammed',
    'website': 'https://github.com/nightman19',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/room_wizard_views.xml',
        'views/room_views.xml',
        'views/booking_views.xml',
        'views/payment_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

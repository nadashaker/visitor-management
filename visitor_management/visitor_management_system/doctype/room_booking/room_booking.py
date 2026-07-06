# Copyright (c) 2026, me and contributors
# For license information, please see license.txt

# Copyright (c) 2026, me and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import timedelta


class RoomBooking(Document):

    def validate(self):
        self.check_booking_conflict()

    def check_booking_conflict(self):

        existing_bookings = frappe.get_all(
            "Room Booking",
            filters={
                "room": self.room,
                "booking_date": self.booking_date,
                "status": ["in", ["Approved", "Pending Approval"]],
                "name": ["!=", self.name]
            },
            fields=["name", "start_time", "end_time"]
        )

        # Convert current booking times to timedelta
        current_start = self.to_timedelta(self.start_time)
        current_end = self.to_timedelta(self.end_time)

        for booking in existing_bookings:

            booking_start = booking.start_time
            booking_end = booking.end_time

            # If the values are strings, convert them
            if isinstance(booking_start, str):
                booking_start = self.to_timedelta(booking_start)

            if isinstance(booking_end, str):
                booking_end = self.to_timedelta(booking_end)

            if current_start < booking_end and current_end > booking_start:
                frappe.throw(
                    _("This room is already booked during the selected time.")
                )

    def to_timedelta(self, time_value):
        """Convert HH:MM:SS string or timedelta into timedelta"""

        if isinstance(time_value, timedelta):
            return time_value

        hours, minutes, seconds = map(int, str(time_value).split(":"))

        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )
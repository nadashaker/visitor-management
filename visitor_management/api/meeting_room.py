import frappe
from frappe import _
from datetime import timedelta


def to_timedelta(time_value):
    """
    Convert HH:MM:SS string or timedelta into timedelta
    """

    if isinstance(time_value, timedelta):
        return time_value

    hours, minutes, seconds = map(int, str(time_value).split(":"))

    return timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds
    )


# ============================================================
# API 1 - Get Available Rooms
# ============================================================

@frappe.whitelist()
def get_available_rooms(booking_date=None, start_time=None, end_time=None):

    if not booking_date or not start_time or not end_time:
        frappe.throw(
            _("Booking Date, Start Time and End Time are required.")
        )

    requested_start = to_timedelta(start_time)
    requested_end = to_timedelta(end_time)

    if requested_start >= requested_end:
        frappe.throw(
            _("Start Time must be before End Time.")
        )

    rooms = frappe.get_all(
        "Meeting Room",
        filters={
            "status": "Available"
        },
        fields=[
            "name",
            "room_name",
            "capacity",
            "location",
            "facilities",
            "status"
        ]
    )

    available_rooms = []

    for room in rooms:

        bookings = frappe.get_all(
            "Room Booking",
            filters={
                "room": room.name,
                "booking_date": booking_date,
                "status": ["in", ["Approved", "Pending Approval"]]
            },
            fields=[
                "start_time",
                "end_time"
            ]
        )

        room_available = True

        for booking in bookings:

            booking_start = to_timedelta(booking.start_time)
            booking_end = to_timedelta(booking.end_time)

            if (
                requested_start < booking_end
                and requested_end > booking_start
            ):
                room_available = False
                break

        if room_available:

            available_rooms.append({
                "room_name": room.room_name,
                "capacity": room.capacity,
                "location": room.location,
                "facilities": room.facilities,
                "status": room.status
            })

    return {
        "success": True,
        "available_rooms": available_rooms
    }


# ============================================================
# API 2 - Create Room Booking
# ============================================================

@frappe.whitelist()
def create_room_booking(
    meeting_title=None,
    room=None,
    requested_by=None,
    booking_date=None,
    start_time=None,
    end_time=None,
    purpose=None
):

    if not all([
        meeting_title,
        room,
        requested_by,
        booking_date,
        start_time,
        end_time
    ]):
        frappe.throw(_("All required fields are required."))

    if not frappe.db.exists("Meeting Room", room):
        frappe.throw(_("Meeting Room does not exist."))

    room_doc = frappe.get_doc("Meeting Room", room)

    if room_doc.status != "Available":
        frappe.throw(_("Meeting Room is not available."))

    requested_start = to_timedelta(start_time)
    requested_end = to_timedelta(end_time)

    if requested_start >= requested_end:
        frappe.throw(_("Start Time must be before End Time."))

    bookings = frappe.get_all(
        "Room Booking",
        filters={
            "room": room,
            "booking_date": booking_date,
            "status": ["in", ["Approved", "Pending Approval"]]
        },
        fields=[
            "start_time",
            "end_time"
        ]
    )

    for booking in bookings:

        booking_start = to_timedelta(booking.start_time)
        booking_end = to_timedelta(booking.end_time)

        if (
            requested_start < booking_end
            and requested_end > booking_start
        ):
            frappe.throw(
                _("This room is already booked during the selected time.")
            )

    booking = frappe.get_doc({
        "doctype": "Room Booking",
        "meeting_title": meeting_title,
        "room": room,
        "requested_by": requested_by,
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "purpose": purpose,
        "status": "Draft"
    })

    booking.insert(ignore_permissions=True)

    return {
        "success": True,
        "message": "Room Booking created successfully.",
        "booking_id": booking.name
    }


# ============================================================
# API 3 - Get Booking Details
# ============================================================

@frappe.whitelist()
def get_booking_details(booking_id=None):

    if not booking_id:
        frappe.throw(_("booking_id is required."))

    if not frappe.db.exists("Room Booking", booking_id):
        frappe.throw(_("Booking not found."))

    booking = frappe.get_doc("Room Booking", booking_id)

    return {
        "success": True,
        "booking": {
            "booking_id": booking.name,
            "meeting_title": booking.meeting_title,
            "room": booking.room,
            "requested_by": booking.requested_by,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "purpose": booking.purpose,
            "status": booking.status
        }
    }


# ============================================================
# API 4 - Get My Bookings
# ============================================================

@frappe.whitelist()
def get_my_bookings(
    employee=None,
    from_date=None,
    to_date=None,
    status=None
):

    if not employee:
        frappe.throw(_("Employee is required."))

    filters = {
        "requested_by": employee
    }

    if from_date and to_date:
        filters["booking_date"] = ["between", [from_date, to_date]]

    elif from_date:
        filters["booking_date"] = [">=", from_date]

    elif to_date:
        filters["booking_date"] = ["<=", to_date]

    if status:
        filters["status"] = status

    bookings = frappe.get_all(
        "Room Booking",
        filters=filters,
        fields=[
            "name",
            "meeting_title",
            "room",
            "booking_date",
            "start_time",
            "end_time",
            "status"
        ],
        order_by="booking_date asc"
    )

    return {
        "success": True,
        "bookings": bookings
    }


# ============================================================
# API 5 - Cancel Booking
# ============================================================

@frappe.whitelist()
def cancel_booking(
    booking_id=None,
    cancellation_reason=None
):

    if not booking_id:
        frappe.throw(_("booking_id is required."))

    if not frappe.db.exists("Room Booking", booking_id):
        frappe.throw(_("Booking not found."))

    booking = frappe.get_doc("Room Booking", booking_id)

    if booking.status == "Completed":
        frappe.throw(_("Completed bookings cannot be cancelled."))

    if not frappe.has_permission(
        "Room Booking",
        "write",
        booking
    ):
        frappe.throw(_("You do not have permission to cancel this booking."))

    booking.status = "Cancelled"

    #if hasattr(booking, "cancellation_reason"):
    #    booking.cancellation_reason = cancellation_reason

    booking.save(ignore_permissions=True)

    return {
        "success": True,
        "message": "Booking cancelled successfully."
    }
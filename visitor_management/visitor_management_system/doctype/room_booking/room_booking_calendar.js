frappe.views.calendar["Room Booking"] = {

    field_map: {

        start: "booking_date",

        end: "booking_date",

        id: "name",

        title: "meeting_title",

        status: "status",

        color: "status"

    },

    filters: [

        {
            fieldtype: "Select",
            fieldname: "status",
            options: "Approved"
        }

    ]

};
# Copyright (c) 2026, me and contributors
# For license information, please see license.txt

# import frappe
import frappe
import qrcode
import os

from frappe.model.document import Document
from frappe.utils.file_manager import save_file


class visitrequest(Document):

    def before_save(self):

        frappe.msgprint("Before Save Running")

    def on_update(self):

        frappe.msgprint("After Save Running")

        qr_data = f"""
Visitor Name: {self.visitorname}
Visitor ID: {self.visitorid}
Pass Status: {self.pass_status}
Visit Request: {self.name}
"""

        qr = qrcode.make(qr_data)

        file_name = f"{self.name}_qr.png"

        file_path = f"/tmp/{file_name}"

        qr.save(file_path)

        with open(file_path, "rb") as f:

            saved_file = save_file(
                file_name,
                f.read(),
                self.doctype,
                self.name,
                is_private=0
            )

        self.db_set("qr_code", saved_file.file_url)
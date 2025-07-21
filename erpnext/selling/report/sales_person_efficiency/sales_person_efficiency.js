// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Person Efficiency"] = {
	"filters": [
		{
			"fieldname": "from_year",
			"label": "From Year",
			"fieldtype": "Int",
			"default": frappe.datetime.get_today().split("-")[0] - 1,
			"reqd": 1
		},
		{
			"fieldname": "to_year",
			"label": "To Year",
			"fieldtype": "Int",
			"default": frappe.datetime.get_today().split("-")[0],
			"reqd": 1
		},
		{
			"fieldname": "from_month",
			"label": "From Month",
			"fieldtype": "Select",
			"options": [
				"January", "February", "March", "April", "May", "June",
				"July", "August", "September", "October", "November", "December"
			],
			"default": "January",
			"reqd": 1
		},
		{
			"fieldname": "to_month",
			"label": "To Month",
			"fieldtype": "Select",
			"options": [
				"January", "February", "March", "April", "May", "June",
				"July", "August", "September", "October", "November", "December"
			],
			"default": "December",
			"reqd": 1
		},
		{
			"fieldname": "sales_person",
			"label": "Sales Person",
			"fieldtype": "Link",
			"options": "Sales Person"
		}
		// {
		// 	"fieldname": "customer",
		// 	"label": "Customer",
		// 	"fieldtype": "Link",
		// 	"options": "Customer"
		// }
	]
};

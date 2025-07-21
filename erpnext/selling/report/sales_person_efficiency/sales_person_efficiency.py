import frappe
from frappe import _
from collections import defaultdict
import calendar


def execute(filters=None):
	if not filters:
		filters = {}

	columns, month_keys = get_columns(filters)
	data, totals = get_data(filters, month_keys)

	# Add grand total row
	if data:
		grand_total_row = {"sales_person": "Total"}
		for col in columns:
			fieldname = col.get("fieldname")
			if fieldname and fieldname != "sales_person":
				grand_total_row[fieldname] = sum(row.get(fieldname, 0) for row in data)
		data.append(grand_total_row)

	return columns, data


def get_columns(filters):
	columns = [{
		"label": _("Sales Person"),
		"fieldname": "sales_person",
		"fieldtype": "Link",
		"options": "Sales Person",
		"width": 180
	}]

	from_year = int(filters.get("from_year"))
	to_year = int(filters.get("to_year"))
	from_month = list(calendar.month_name).index(filters.get("from_month"))
	to_month = list(calendar.month_name).index(filters.get("to_month"))

	month_keys = []  # To track order and keys
	for year in range(from_year, to_year + 1):
		start_month = from_month if year == from_year else 1
		end_month = to_month if year == to_year else 12
		for month in range(start_month, end_month + 1):
			label = f"{calendar.month_name[month]} {year}"
			slug = f"{calendar.month_name[month].lower()}_{year}"
			month_keys.append(slug)

			columns.extend([
				{"label": f"{label} - On Time", "fieldname": f"{slug}_on_time", "fieldtype": "Int", "width": 181},
				{"label": f"{label} - Delay ≤ 4", "fieldname": f"{slug}_delay_short", "fieldtype": "Int", "width": 192},
				{"label": f"{label} - Delay > 4", "fieldname": f"{slug}_delay_long", "fieldtype": "Int", "width": 192},
				{"label": f"{label} - Total", "fieldname": f"{slug}_monthly_total", "fieldtype": "Int", "width": 180},
			])

	# Final cumulative total column
	columns.append({
		"label": "Overall Deliveries",
		"fieldname": "Overall_deliveries",
		"fieldtype": "Int",
		"width": 140
	})

	return columns, month_keys


def get_data(filters, month_keys):
	query = """
		SELECT 
			st.sales_person,
			MONTH(dn.posting_date) AS month,
			YEAR(dn.posting_date) AS year,
			DATEDIFF(dn.posting_date, soi.delivery_date) AS delay
		FROM `tabDelivery Note` dn
		JOIN `tabDelivery Note Item` dni ON dn.name = dni.parent
		JOIN `tabSales Order Item` soi ON soi.name = dni.so_detail
		JOIN `tabSales Order` so ON so.name = soi.parent
		JOIN `tabSales Team` st ON st.parent = so.name
		WHERE 
			dn.docstatus = 1 AND so.docstatus = 1 AND st.parenttype = 'Sales Order'
	"""

	conditions = []
	values = []

	if filters.get("sales_person"):
		conditions.append("st.sales_person = %s")
		values.append(filters.get("sales_person"))

	if filters.get("customer"):
		conditions.append("so.customer = %s")
		values.append(filters.get("customer"))

	if conditions:
		query += " AND " + " AND ".join(conditions)

	rows = frappe.db.sql(query, values, as_dict=1)

	summary = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))  # {sales_person: {month_key: [on_time, short, long]}}

	for row in rows:
		if not row.sales_person or not row.month or not row.year:
			continue
		key = f"{calendar.month_name[row.month].lower()}_{row.year}"
		if row.delay <= 0:
			summary[row.sales_person][key][0] += 1
		elif row.delay <= 4:
			summary[row.sales_person][key][1] += 1
		else:
			summary[row.sales_person][key][2] += 1

	data = []

	for sp, months in summary.items():
		row = {"sales_person": sp}
		Overall_deliveries = 0
		for key in month_keys:
			on_time = months.get(key, [0, 0, 0])[0]
			delay_short = months.get(key, [0, 0, 0])[1]
			delay_long = months.get(key, [0, 0, 0])[2]
			monthly_total = on_time + delay_short + delay_long

			row[f"{key}_on_time"] = on_time
			row[f"{key}_delay_short"] = delay_short
			row[f"{key}_delay_long"] = delay_long
			row[f"{key}_monthly_total"] = monthly_total

			Overall_deliveries += monthly_total

		row["Overall_deliveries"] = Overall_deliveries	
		data.append(row)

	return data, summary

import frappe
from frappe import _
from collections import defaultdict
import calendar


def execute(filters=None):
	if not filters:
		filters = {}

	columns, month_keys = get_columns(filters)
	data = prepare_report_data(filters, month_keys)

	return columns, data


def get_columns(filters):
	base_columns = get_base_column()
	from_year, to_year, from_month, to_month = extract_date_filters(filters)
	month_keys = get_month_keys(from_year, to_year, from_month, to_month)
	month_columns = build_monthly_columns(month_keys)
	final_column = get_final_total_column()

	return base_columns + month_columns + [final_column], month_keys


def get_base_column():
	return [{
		"label": _("Sales Person"),
		"fieldname": "sales_person",
		"fieldtype": "Link",
		"options": "Sales Person",
		"width": 180
	}]


def extract_date_filters(filters):
	from_year = int(filters.get("from_year"))
	to_year = int(filters.get("to_year"))
	from_month = list(calendar.month_name).index(filters.get("from_month"))
	to_month = list(calendar.month_name).index(filters.get("to_month"))
	return from_year, to_year, from_month, to_month


def get_month_keys(from_year, to_year, from_month, to_month):
	month_keys = []
	for year in range(from_year, to_year + 1):
		start = from_month if year == from_year else 1
		end = to_month if year == to_year else 12
		for month in range(start, end + 1):
			month_keys.append(f"{calendar.month_name[month].lower()}_{year}")
	return month_keys


def build_monthly_columns(month_keys):
	columns = []
	for key in month_keys:
		month, year = key.split("_")
		label = f"{month.title()} {year}"
		columns.extend([
			{"label": f"{label} - On Time", "fieldname": f"{key}_on_time", "fieldtype": "Int", "width": 181},
			{"label": f"{label} - Delay ≤ 4", "fieldname": f"{key}_delay_short", "fieldtype": "Int", "width": 192},
			{"label": f"{label} - Delay > 4", "fieldname": f"{key}_delay_long", "fieldtype": "Int", "width": 192},
			{"label": f"{label} - Total", "fieldname": f"{key}_monthly_total", "fieldtype": "Int", "width": 180},
		])
	return columns


def get_final_total_column():
	return {
		"label": "Overall Deliveries",
		"fieldname": "Overall_deliveries",
		"fieldtype": "Int",
		"width": 140
	}

def prepare_report_data(filters, month_keys):
	raw_data = fetch_delivery_data(filters)
	summary = aggregate_delivery_data(raw_data)
	data = build_data_rows(summary, month_keys)
	append_grand_total_row(data)
	return data


def fetch_delivery_data(filters):
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

	return frappe.db.sql(query, values, as_dict=True)


def aggregate_delivery_data(rows):
	summary = {}  # plain dictionary

	for row in rows:
		if not (row.sales_person and row.month and row.year):
			continue

		sales_person = row.sales_person
		key = f"{calendar.month_name[row.month].lower()}_{row.year}"

		if sales_person not in summary:
			summary[sales_person] = {}

		if key not in summary[sales_person]:
			summary[sales_person][key] = [0, 0, 0]
			
		if row.delay <= 0:
			summary[sales_person][key][0] += 1
		elif row.delay <= 4:
			summary[sales_person][key][1] += 1
		else:
			summary[sales_person][key][2] += 1
	return summary


def build_data_rows(summary, month_keys):
	data = []
	for sp, months in summary.items():
		row = {"sales_person": sp}
		overall = 0
		for key in month_keys:
			on_time, short, long = months.get(key, [0, 0, 0])
			total = on_time + short + long
			row.update({
				f"{key}_on_time": on_time,
				f"{key}_delay_short": short,
				f"{key}_delay_long": long,
				f"{key}_monthly_total": total
			})
			overall += total
		row["Overall_deliveries"] = overall
		data.append(row)
	return data


def append_grand_total_row(data):
	if not data:
		return

	grand_total = {"sales_person": "Total"}
	for row in data:
		for key, value in row.items():
			if key != "sales_person":
				grand_total[key] = grand_total.get(key, 0) + value
	data.append(grand_total)

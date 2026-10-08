// Variables for use when pasting generate_error_message.js
// into a given screen's error modal

// /client
const screenDatum = "client"
const screenPath = "/client"
const fieldDisplays = {
  "id": "ID",
  "client_name": "Client Name",
}

// /consumable
const screenDatum = "consumable"
const screenPath = "/consumable"
const fieldDisplays = {
  "consumable_name": "Consumable Name",
  "default_unit_cost_gbp": "Default Unit Cost (GBP)"
}

// /direct-cost
const screenDatum = "direct cost"
const screenPath = "/direct-cost"
const fieldDisplays = {
  "service_id": "Service ID",
  "consumable_id": "Consumable ID",
  "cost_gbp": "Cost (GBP)",
}

// /tender
const screenDatum = "tender"
const screenPath = "/tender"
const fieldDisplays = {
  "id": "ID",
  "tender_title": "Tender Title",
  "client_id": "Client ID",
  "projected_sales_value_gbp": "Projected Sales Value (GBP)",
}


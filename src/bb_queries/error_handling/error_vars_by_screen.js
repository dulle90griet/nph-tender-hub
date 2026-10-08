// Variables for use when pasting generate_error_message.js
// into a given screen's error modal

// /client
const screenDatum = "client";
const screenPath = "/client";
const fieldDisplays = {
  "id": "ID",
  "client_name": "Client Name",
};

// /consumable
const screenDatum = "consumable";
const screenPath = "/consumable";
const fieldDisplays = {
  "consumable_name": "Consumable Name",
  "default_unit_cost_gbp": "Default Unit Cost (GBP)"
};

// /direct-cost
const screenDatum = "direct cost";
const screenPath = "/direct-cost";
const fieldDisplays = {
  "service_id": "Service ID",
  "consumable_id": "Consumable ID",
  "cost_gbp": "Cost (GBP)",
};;

// /job-title
const screenDatum = "job title";
const screenPath = "/job-title";
const fieldDisplays = {
  "id": "ID",
  "department_id": "Department ID",
  "title": "Title",
  "default_ft_weekly_hours": "Default FT Weekly Hours",
  "default_luncH_break_hours": "Default Lunch Break Hours",
  "hourly_rate_gbp": "Hourly Rate (GBP)",
  "default_annual_holiday_days": "Default Annual Holiday Days",
  "default_annual_training_days": "Default Annual Training Days",
  "default_annual_sick_days": "Default Annual Sick Days",
};

// /labour-cost
const screenDatum = "labour cost";
const screenPath = "/labour-cost";
const fieldDisplays = {
  "service_id": "Service ID",
  "title_engaged_id": "Title Engaged ID",
  "required_time_mins": "Required Time (Mins)",
};

// /tender
const screenDatum = "tender";
const screenPath = "/tender";
const fieldDisplays = {
  "id": "ID",
  "tender_title": "Tender Title",
  "client_id": "Client ID",
  "projected_sales_value_gbp": "Projected Sales Value (GBP)",
};


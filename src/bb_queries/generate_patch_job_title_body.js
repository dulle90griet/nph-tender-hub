let bodyStr = "{";
const clickedRow = JSON.parse($("State.clickedRow"));
const formValues = $("[Update Job Title Form].Value");
const columnNames = [
  "title",
  "default_ft_weekly_hours",
  "default_lunch_break_hours",
  "hourly_rate_gbp",
  "default_annual_holiday_days",
  "default_annual_training_days",
  "default_annual_sick_days"
];
const updatedRows = [];

if (formValues["department"] == "I want to add a new department") {
  if (formValues["new_department"] != JSON.parse($("State.clickedRow")).department) {
    updatedRows.push(`"department": "${formValues["new_department"]}"`);
  }
} else if (formValues["department"] != JSON.parse($("State.clickedRow")).department) {
  updatedRows.push(`"department": "${formValues["department"]}"`);
}

for (let columnName of columnNames) {
  if (formValues[columnName] != clickedRow[columnName]) {
    updatedRows.push(`"${columnName}": "${formValues[columnName]}"`);
  }
}

bodyStr += updatedRows.join(", ");
bodyStr += "}";

return bodyStr;

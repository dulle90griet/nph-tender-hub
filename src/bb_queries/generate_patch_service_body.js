let bodyStr = "{";
const clickedRow = JSON.parse($("State.clickedRow"));
const formValues = $("[Update Service Form].Value");
const columnNames = [
  "pillar"
  ,"category"
  ,"service_name"
  ,"xero_code"
  ,"overhead_recovery_on_labour_percentage"
  ,"required_profit_margin_percentage"
  ,"acceptable_market_price_gbp"
  ,"our_current_unit_price_gbp"
  ,"new_unit_price_gbp"
  ,"new_day_rate_gbp"
  ,"comments"
];
const updatedRows = [];

for (let columnName of columnNames) {
  if (formValues[columnName] != clickedRow[columnName]) {
    updatedRows.push(`"${columnName}": "${formValues[columnName]}"`);
  }
}

bodyStr += updatedRows.join(", ");
bodyStr += "}";

return bodyStr;

let bodyStr = "{";
const clickedRow = JSON.parse($("State.clickedRow"));
const formValues = $("[Update Consumable Form].Value");
const columnNames = [
  "consumable_name",
  "default_unit_cost_gbp"
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

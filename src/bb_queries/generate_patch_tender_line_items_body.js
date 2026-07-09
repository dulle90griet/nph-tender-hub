let bodyStr = "{";
const clickedRow = JSON.parse($("State.clickedRow"));
const formValues = $("[Update Line Item Form].Value");
const columnNames = [
  "total_number_pa",
  "unit_price_override_gbp"
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

let bodyStr = "{";
const clickedRow = JSON.parse($("State.clickedRow"));
const formValues = $("[Update Labour Cost Form].Value");
const columnNames = [
  "required_time_mins"
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

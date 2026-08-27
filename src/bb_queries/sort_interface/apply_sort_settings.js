// On-click code for the 'Apply' button in the sort config interface.
//
// Parses the current sortConditions array into an API-ready
// query parameters string.
//
// Used in 'Update State' -> 'Set value' -> 'sortParam'.


const conditions = JSON.parse($("State.sortConditions"));
const sortParams = [];
for (let c of conditions) {
  if (c.column.length === 0) {
    continue;
  }
  let directionMark = c.direction.toUpperCase() === "DESC" ? "-" : "";
  sortParams.push(directionMark + c.column);
}
return sortParams.join(",");

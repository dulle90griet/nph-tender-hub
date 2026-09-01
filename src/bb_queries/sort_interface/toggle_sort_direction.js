// On-click code for the ASC / DESC toggle button pair in the sort config interface.
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.sortConditions"));
const index = $("[SortParams Repeater].[Row index]");
conditions[index].direction = conditions[index].direction.toUpperCase() === "desc" ? "ASC" : "DESC";
return JSON.stringify(conditions);

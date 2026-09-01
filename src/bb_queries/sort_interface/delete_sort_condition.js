// On-click code for 'delete sort condition' buttons in the sort
// config interface.
//
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.sortConditions"));
const index = $("[SortParams Repeater].[Row index]");
conditions.splice(index, 1);
return JSON.stringify(conditions);

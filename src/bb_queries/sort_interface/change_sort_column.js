// On-click code for column pickers in the sort config interface.
//
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.sortConditions"));
const index = $("[SortParams Repeater].[Row index]");
conditions[index].column = $("[Sort Condition Form].Fields.column");
return JSON.stringify(conditions);

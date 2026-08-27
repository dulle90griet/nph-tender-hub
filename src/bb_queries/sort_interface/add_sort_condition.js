// On-click code for 'add sort condition' button in the sort
// config interface.
//
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.sortConditions"));
if (conditions.length < $("State.maxSortConditions")) {
  conditions.push({"column": "", "direction": "ASC"});
}
return JSON.stringify(conditions);

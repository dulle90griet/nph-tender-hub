// On-click code for 'add search' button in the search interface.
//
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.searchValues"));
if (conditions.length < 1) {
  conditions.push({"searchColumn": "", "searchString": ""});
}
return JSON.stringify(conditions);

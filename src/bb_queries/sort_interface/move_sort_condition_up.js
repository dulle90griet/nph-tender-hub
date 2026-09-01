// On-click code for the 'move sort condition up' button in
// the sort config interface.
//
// Used in 'Update State' -> 'Set value' -> 'sortConditions'.

const conditions = JSON.parse($("State.sortConditions"));
const index = $("[SortParams Repeater].[Row index]");
if (index > 0) {
  const temp = conditions[index];
  conditions[index] = conditions[index - 1];
  conditions[index - 1] = temp;
}
return JSON.stringify(conditions);

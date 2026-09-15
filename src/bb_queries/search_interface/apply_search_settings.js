// On-click code for the 'Apply' button in the search interface.
//
// Parses the current searchValues array into API-ready query
// parameters strings.

// Used in 'Update State' -> 'Set value' -> 'searchColumn'

const conditions = JSON.parse($("State.searchValues"));

if (conditions.length > 0 && conditions[0]["searchColumn"]) {
  return conditions[0]["searchColumn"];
}
return "";

// Used in 'Update State' -> 'Set value' -> 'searchString'

const conditions = JSON.parse($("State.searchValues"));

if (conditions.length > 0 && conditions[0]["searchColumn"]) {
  return conditions[0]["searchString"] ?? "";
}
return "";


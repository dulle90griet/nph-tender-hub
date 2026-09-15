// Code for search-enabled tables' and data providers'
// query bindings.
//
// Parses the State.searchParams JSON string to extract
// either the searchColumn or the searchString.

// Used in the 'searchColumn' query binding

if ($("State.searchParams")) {
  return JSON.parse($("State.searchParams")).searchColumn ?? "";
} else {
  return "";
}

// Used in the 'searchString' query binding

if ($("State.searchParams")) {
  return JSON.parse($("State.searchParams")).searchString ?? "";
} else {
  return "";
}

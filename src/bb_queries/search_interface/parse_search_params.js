// Code for search-enabled tables' and data providers'
// query bindings.
//
// Parses the State.searchParams JSON string to extract
// either the searchColumn or the searchString.
//
// Note that in every case "State.searchParams" should be replaced
// with the name of a state variable used only on the present screen.
// Otherwise, persistence of app state between screens can cause
// unexpected behaviours.

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

// Code for the 'last search' button's enable/disable logic
//
// Returns true if the button should be enabled,
// and false if it should be disabled

if ($("State.searchFormValues")) {
  return JSON.parse($("State.searchFormValues")).length;
} else {
  return 0;
}

if ($("State.searchParams") && $("State.searchFormValues")) {
  const searchParams = JSON.parse($("State.searchParams"));
  const searchParamsColumn = searchParams.searchColumn ?? "";
  const searchParamsString = searchParams.searchString ?? "";

  if($("[Search Form].Fields.search_column") != searchParamsColumn ||
     $("[Search Form].Fields.search_string") != searchParamsString) {
    return true
  }
  return false
}

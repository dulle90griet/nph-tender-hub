// Code used to generate the error modal's display text on each screen.

// A string describing whatever a single row in the current screen's table
// represents, e.g. "consumable" for the /consumable screen
const screenDatum = "row"; 
// The path of the current screen
const screenPath = "/screen";
// A map of column names in the database and their human-friendly versions
const fieldDisplays = {"column_name": "column_display_name"};

const currentTime = new Date();
const genericMessage = `contact your administrator with the following information:\n\n- **Screen**: ${screenPath}\n- **Timestamp**: ${currentTime}`;
const type409 = "\n\n- **Error**: 409";
const type422 = "\n\n- **Error**: 422";

if (typeof $("State.queryResult") === 'undefined' ||
    typeof $("State.queryResult").data === 'undefined') {
  return `An error was encountered, but no response data was received.\n\nPlease ${genericMessage}`;
}

if (($("State.queryResult").data[0]?.statusCode ?? null) === 422) {
  const fieldName = $("State.queryResult").data[0]?.detail?.[0]?.loc?.at(-1) ?? null;
  const fieldDisplay = fieldDisplays[fieldName] ?? null;
  if (fieldDisplay !== null) {
    return `Invalid value supplied for ${fieldDisplay}. Please check the limits described in the form.`;
  } else {
    return `An error was encountered, but the details were not recognised.\n\n Please ${genericMessage}${type422}`;
  }
} else if (($("State.queryResult").data[0]?.statusCode ?? null) === 409) {
  const message = $("State.queryResult").data[0]?.detail?.[0]?.message ?? null;
  const messageDetail = String(message).match(/Key \(([\w\d\s\_\,]+)\)=\(([\w\d\s\_\,]+)\) already exists./);

  if (!messageDetail) {
    const text = `A Unique Violation was encountered, meaning a ${screenDatum} with those values already exists.`;
    text += "\n\nNormally the server would tell us more than that, but in this case it hasn't.";
    text += `\n\nTry entering a ${screenDatum} with different identifying values. If the problem persists, please ${genericMessage}${type409}`;
    return text;

  } else {
    const [, keysString, valuesString] = messageDetail;
    const keys = keysString.replace(/, /g, ",").split(",");
    const values = valuesString.replace(/, /g, ",").split(",");
    const valuesListable = keys.length === values.length;

    let errMsg = `A ${screenDatum} with ${valuesListable ? "" : "that combination of "}`;
    for (let i = 0; i < keys.length; i++) {
      const keyDisplay = fieldDisplays[keys[i]] ?? keys[i];
      if (keys.length > 1 && i === keys.length - 1) {
        errMsg += " and ";
      }
      errMsg += valuesListable ? `${keyDisplay} = '${values[i]}'` : `${keyDisplay}`;
      if (i < keys.length - 2) {
        errMsg += ", ";
      }
    }
    errMsg += " already exists.";

    return errMsg;
  }
}

return null;

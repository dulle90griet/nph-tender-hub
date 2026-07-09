const value = $("[New Repeater].GET /tender.projected_sales_value_gbp").toLocaleString("en-GB");
const created = new Date($("[New Repeater].GET /tender.date_created")).toLocaleString("en-GB");
return `Projected value: £${value}<br />Created: ${created}`;
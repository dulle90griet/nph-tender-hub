function padTo2Digits(num) {
  return num.toString().padStart(2, "0");
}

const created = new Date($("[Tender Info Repeater].GET /tender/single.date_created"));
const created_date = [
  padTo2Digits(created.getDate()),
  padTo2Digits(created.getMonth() + 1),
  created.getFullYear(),
].join('/');
return `__Date Created:__ ${created_date}`;

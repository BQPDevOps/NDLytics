import moment from 'moment';

function calcNumberOfDays(date1, date2, fallbackDate) {
  let start, end;

  // If date1 is empty, use fallbackDate minus 1 month as start date
  if (!date1) {
    start = moment(fallbackDate).subtract(1, 'month');
  } else {
    start = moment(date1);
  }

  end = moment(date2);

  // Calculate difference in days between start and end dates
  const diffInDays = end.diff(start, 'days');

  return diffInDays;
}
export default calcNumberOfDays;

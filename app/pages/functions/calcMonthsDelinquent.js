import moment from 'moment';
import PropTypes from 'prop-types';

const calcMonthsDelinquent = (
  nextDueDate,
  expirationDate,
  consoleDebug = false
) => {
  const startDate = moment(
    moment(nextDueDate).subtract(1, 'months').format('YYYY-MM-DD')
  );

  const endDate = moment(moment(expirationDate).format('YYYY-MM-DD'));

  const diffYears = endDate.diff(startDate, 'years');

  startDate.add(diffYears, 'years');

  const diffMonths = endDate.diff(startDate, 'months');

  if (consoleDebug) {
    console.log('MONTH DELINQUENT-------------------------------');
    console.log('Months Delinquent: ', diffYears * 12 + diffMonths);
    console.log('----------------------------------------------');
  }
  return diffYears * 12 + diffMonths;
};
export default calcMonthsDelinquent;

calcMonthsDelinquent.propTypes = {
  nextDueDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

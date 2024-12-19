import calcNumberOfDays from './calcNumberOfDays';
import moment from 'moment';
import PropTypes from 'prop-types';

const calcLastPaidToResolution = (
  nextDueDate,
  expirationDate,
  lastPaidDate,
  consoleDebug = false
) => {
  const startDate = moment(nextDueDate).isValid()
    ? moment(nextDueDate).subtract(1, 'months').format('YYYY-MM-DD')
    : moment(lastPaidDate).format('YYYY-MM-DD');
  if (consoleDebug) {
    console.log('LAST PAID TO RESOLUTION------------------------');
    console.log(
      'LastPaidToResolution: ',
      calcNumberOfDays(startDate, expirationDate)
    );
    console.log('nextDueDate: ', nextDueDate);
    console.log('expirationDate: ', expirationDate);
    console.log('lastPaidDate: ', lastPaidDate);
    console.log('----------------------------------------------');
  }
  return calcNumberOfDays(startDate, expirationDate);
};
export default calcLastPaidToResolution;

calcLastPaidToResolution.propTypes = {
  nextDueDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  lastPaidDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

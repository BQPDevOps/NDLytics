import moment from 'moment';
import PropTypes from 'prop-types';

const calcFirstPaymentDueDate = (downPayment, expirationDate, consoleDebug) => {
  if (downPayment === 0) expirationDate;
  if (consoleDebug) {
    console.log('FIRST PAYMENT DUE DATE------------------------');
    console.log(
      'First Payment Due Date: ',
      new Date(moment(expirationDate).add(1, 'months').format('MM/DD/YYYY'))
    );
    console.log('downPayment: ', downPayment);
    console.log('expirationDate: ', expirationDate);
    console.log('----------------------------------------------');
  }
  return new Date(moment(expirationDate).add(1, 'months').format('MM/DD/YYYY'));
};

export default calcFirstPaymentDueDate;

calcFirstPaymentDueDate.defaultProps = {
  downPayment: 0,
  expirationDate: '',
  consoleDebug: false,
};

calcFirstPaymentDueDate.propTypes = {
  downPayment: PropTypes.number.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

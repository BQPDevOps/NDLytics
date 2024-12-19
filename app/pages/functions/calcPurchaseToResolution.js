import calcNumberOfDays from './calcNumberOfDays';
import PropTypes from 'prop-types';

const calcPurchaseToResolution = (
  purchaseDate,
  expirationDate,
  consoleDebug
) => {
  if (consoleDebug) {
    console.log('PURCHASE TO RESOLUTION--------------------------');
    console.log(
      'Purchase to Resolution: ',
      calcNumberOfDays(purchaseDate, expirationDate)
    );
    console.log('----------------------------------------------');
  }
  return calcNumberOfDays(purchaseDate, expirationDate);
};
export default calcPurchaseToResolution;

calcPurchaseToResolution.defaultProps = {
  purchaseDate: '',
  expirationDate: '',
  consoleDebug: false,
};

calcPurchaseToResolution.propTypes = {
  purchaseDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

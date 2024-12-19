import PropTypes from 'prop-types';

const calcTotalExpenses = (purchasePrice, legalFees, consoleDebug) => {
  if (consoleDebug) {
    console.log('TOTAL EXPENSES----------------------------------');
    console.log('Total Expenses: ', purchasePrice + legalFees + 250);
    console.log('----------------------------------------------');
  }
  return purchasePrice + legalFees + 250;
};
export default calcTotalExpenses;

calcTotalExpenses.defaultProps = {
  purchasePrice: 0,
  legalFees: 0,
  consoleDebug: false,
};

calcTotalExpenses.propTypes = {
  purchasePrice: PropTypes.number.isRequired,
  legalFees: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

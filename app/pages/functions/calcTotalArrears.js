import PropTypes from 'prop-types';

const calcTotalArrears = (
  downPayment,
  lastPaidToResolution,
  perDiem,
  defermentType,
  defermentAmount,
  lateFees,
  legalFees,
  defermentAmount02,
  consoleDebug
) => {
  let totalInterest = 0;

  switch (downPayment > 0) {
    case true:
      totalInterest = (lastPaidToResolution + 30) * perDiem;
    default:
      totalInterest = lastPaidToResolution * perDiem;
  }

  if (defermentType === 'forgive') {
    totalInterest -= defermentAmount;
  }

  if (defermentType === 'split') {
    totalInterest -= defermentAmount02;
  }
  if (consoleDebug) {
    console.log('TOTAL ARREARS---------------------------------');
    console.log('Total Arrears: ', totalInterest + lateFees + legalFees);
    console.log('----------------------------------------------');
  }
  return Number((totalInterest + lateFees + legalFees).toFixed(2));
};
export default calcTotalArrears;

calcTotalArrears.defaultProps = {
  downPayment: 0,
  lastPaidToResolution: 0,
  perDiem: 0,
  defermentType: 'none',
  defermentAmount: 0,
  lateFees: 0,
  legalFees: 0,
  defermentAmount02: 0,
  consoleDebug: false,
};

calcTotalArrears.propTypes = {
  downPayment: PropTypes.number.isRequired,
  lastPaidToResolution: PropTypes.number.isRequired,
  perDiem: PropTypes.number.isRequired,
  defermentType: PropTypes.string.isRequired,
  defermentAmount: PropTypes.number.isRequired,
  lateFees: PropTypes.number.isRequired,
  legalFees: PropTypes.number.isRequired,
  defermentAmount02: PropTypes.number,
  consoleDebug: PropTypes.bool,
};

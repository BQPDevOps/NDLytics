import PropTypes from 'prop-types';

const calcTotalDebt = (
  accruedInterest,
  legalFees,
  lateFees,
  currentUPB,
  consoleDebug
) => {
  if (consoleDebug) {
    console.log('TOTAL DEBT--------------------------------------');
    console.log(
      'Total Debt: ',
      accruedInterest + legalFees + lateFees + currentUPB
    );
    console.log('accruedInterest: ', accruedInterest, typeof accruedInterest);
    console.log('legalFees: ', legalFees, typeof legalFees);
    console.log('lateFees: ', lateFees, typeof lateFees);
    console.log('currentUPB: ', currentUPB, typeof currentUPB);
    console.log('----------------------------------------------');
  }
  return Number(
    (accruedInterest + legalFees + lateFees + currentUPB).toFixed(2)
  );
};
export default calcTotalDebt;

calcTotalDebt.defaultProps = {
  accruedInterest: 0,
  legalFees: 0,
  lateFees: 0,
  currentUPB: 0,
  consoleDebug: false,
};

calcTotalDebt.propTypes = {
  accruedInterest: PropTypes.number.isRequired,
  legalFees: PropTypes.number.isRequired,
  lateFees: PropTypes.number.isRequired,
  currentUPB: PropTypes.number.isRequired,
};

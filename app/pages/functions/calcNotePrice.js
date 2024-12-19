import PropTypes from 'prop-types';

const calcNotePrice = (monthlyPayment = 0, term = 0, consoleDebug = false) => {
  const standardYield = 14 / 100 / 12;

  if (consoleDebug) {
    console.log('NOTE PRICE---------------------------------------');
    console.log(
      'Note Price: ',
      (monthlyPayment / standardYield) *
        (1 - Math.pow(1 + standardYield, -(term - 4)))
    );
    console.log('----------------------------------------------');
  }
  return Number(
    (
      (monthlyPayment / standardYield) *
      (1 - Math.pow(1 + standardYield, -(term - 4)))
    ).toFixed(2)
  );
};
export default calcNotePrice;

calcNotePrice.propTypes = {
  monthlyPayment: PropTypes.number.isRequired,
  term: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

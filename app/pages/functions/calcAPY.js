import PropTypes from 'prop-types';

const calcAPY = (
  netProfit = 0,
  totalExpenses = 0,
  purchaseToResolution = 0,
  consoleDebug = false
) => {
  if (consoleDebug) {
    console.log('APY-------------------------------------------');
    console.log(
      'APY: ',
      (Math.exp((totalExpenses + netProfit) / totalExpenses) * 365) /
        ((30 * purchaseToResolution) / 30) -
        1
    );
    console.log('totalExpenses: ', totalExpenses);
    console.log('netProfit: ', netProfit);
    console.log('purchaseToResolution: ', purchaseToResolution);
    console.log('----------------------------------------------');
  }
  return Number(
    (
      (Math.exp((totalExpenses + netProfit) / totalExpenses) * 365) /
        ((30 * purchaseToResolution) / 30) -
      1
    ).toFixed(2)
  );
};
export default calcAPY;

calcAPY.defaultProps = {
  netProfit: 0,
  totalExpenses: 0,
  purchaseToResolution: 0,
  consoleDebug: false,
};

calcAPY.propTypes = {
  netProfit: PropTypes.number.isRequired,
  totalExpenses: PropTypes.number.isRequired,
  purchaseToResolution: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

import PropTypes from 'prop-types';

const calcUPBPurchaseRatio = (
  upb = 0,
  purchasePrice = 0,
  consoleDebug = false
) => {
  if (consoleDebug) {
    console.log('UPB/PURCHASE RATIO------------------------------');
    console.log('UPB / Purchase Price Ratio: ', upb / purchasePrice);
    console.log('UPB: ', upb);
    console.log('Purchase Price: ', purchasePrice);
    console.log('----------------------------------------------');
  }
  return Number((upb / purchasePrice).toFixed(2));
};

export default calcUPBPurchaseRatio;

calcUPBPurchaseRatio.propTypes = {
  upb: PropTypes.number.isRequired,
  purchasePrice: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

import PropTypes from 'prop-types';

const calcCLTV = (seniorUPB, totalDebt, fmv, consoleDebug) => {
  if (consoleDebug) {
    console.log('CLTV------------------------------------------');
    console.log('CLTV: ', (seniorUPB + totalDebt) / fmv);
    console.log('seniorUPB: ', seniorUPB);
    console.log('totalDebt: ', totalDebt);
    console.log('fmv: ', fmv);
    console.log('----------------------------------------------');
  }
  return Number((((seniorUPB + totalDebt) / fmv) * 100).toFixed(2));
};
export default calcCLTV;

calcCLTV.defaultProps = {
  seniorUPB: 0,
  totalDebt: 0,
  fmv: 0,
  consoleDebug: false,
};

calcCLTV.propTypes = {
  seniorUPB: PropTypes.number.isRequired,
  totalDebt: PropTypes.number.isRequired,
  fmv: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

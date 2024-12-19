import PropTypes from 'prop-types';

const calcEquityCoverage = (seniorUPB, fmv, totalDebt, consoleDebug) => {
  if (consoleDebug) {
    console.log('EQUITY COVERAGE------------------------------');
    console.log('Equity Coverage: ', (fmv - seniorUPB) / totalDebt);
    console.log('seniorUPB: ', seniorUPB);
    console.log('fmv: ', fmv);
    console.log('totalDebt: ', totalDebt);
    console.log('----------------------------------------------');
  }
  return Number((((fmv - seniorUPB) / totalDebt) * 100).toFixed(2));
};
export default calcEquityCoverage;

calcEquityCoverage.defaultProps = {
  seniorUPB: 0,
  fmv: 0,
  totalDebt: 0,
  consoleDebug: false,
};

calcEquityCoverage.propTypes = {
  seniorUPB: PropTypes.number.isRequired,
  fmv: PropTypes.number.isRequired,
  totalDebt: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

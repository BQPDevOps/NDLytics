import PropTypes from 'prop-types';

const calcITV = (seniorUPB, notePrice, fmv, consoleDebug) => {
  if (consoleDebug) {
    console.log('ITV-------------------------------------------');
    console.log('ITV: ', (seniorUPB + notePrice) / fmv);
    console.log('seniorUPB: ', seniorUPB);
    console.log('notePrice: ', notePrice);
    console.log('fmv: ', fmv);
    console.log('----------------------------------------------');
  }
  return Number((((seniorUPB + notePrice) / fmv) * 100).toFixed(2));
};
export default calcITV;

calcITV.defaultProps = {
  seniorUPB: 0,
  notePrice: 0,
  fmv: 0,
  consoleDebug: false,
};

calcITV.propTypes = {
  seniorUPB: PropTypes.number.isRequired,
  notePrice: PropTypes.number.isRequired,
  fmv: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

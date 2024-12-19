import PropTypes from 'prop-types';

const checkInterestRate = (interestRate) => {
  if (interestRate > 1) {
    return interestRate / 100;
  }
  if (interestRate < 1) {
    return interestRate;
  }
  return 0;
};

const calcPerDiem = (
  interestRate,
  currentUPB,
  servicer,
  originalInterestRate,
  consoleDebug,
  isSysPerDiem
) => {
  if (consoleDebug) {
    console.log('PER DIEM------------------------------------------');
    console.log('PerDiem Input:');
    console.log('interestRate:', interestRate);
    console.log('currentUPB:', currentUPB);
    console.log('servicer:', servicer);
    console.log('originalInterestRate:', originalInterestRate);
    console.log('isSysPerDiem: ', isSysPerDiem);
  }

  let selectedInterestRate = 0;

  if (isSysPerDiem) {
    selectedInterestRate = originalInterestRate;
  } else {
    selectedInterestRate = interestRate;
  }

  let formattedInterestRate = checkInterestRate(selectedInterestRate);
  switch (servicer) {
    case 'FCI':
      if (consoleDebug) {
        console.log('Per Diem:', (formattedInterestRate * currentUPB) / 360);
        console.log('----------------------------------------------');
      }
      return Number(((formattedInterestRate * currentUPB) / 360).toFixed(2));
    default:
      return Number(((formattedInterestRate * currentUPB) / 365).toFixed(2));
  }
};
export default calcPerDiem;

calcPerDiem.defaultProps = {
  interestRate: 0,
  currentUPB: 0,
  servicer: '',
  originalInterestRate: 0,
  consoleDebug: false,
  isSysPerDiem: true,
};

calcPerDiem.propTypes = {
  interestRate: PropTypes.number.isRequired,
  currentUPB: PropTypes.number.isRequired,
  servicer: PropTypes.string.isRequired,
  originalInterestRate: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
  isSysPerDiem: PropTypes.bool,
};

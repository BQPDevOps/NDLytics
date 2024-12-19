import PropTypes from 'prop-types';

const calcNewUPB = (
  totalArrears = 0,
  currentUPB = 0,
  downPayment = 0,
  defermentAmount = 0,
  defermentType = 'none',
  consoleDebug = false
) => {
  let newUPB = 0;
  if (consoleDebug) console.log('defermentType: ', defermentType);
  switch (defermentType.toUpperCase()) {
    case 'BALLOON':
      if (consoleDebug) {
        console.log('NEW UPB----------------------------------------');
        console.log(
          'BALLOON - NewUPB',
          currentUPB + totalArrears - defermentAmount - downPayment
        );
        console.log('currentUPB: ', currentUPB, typeof currentUPB);
        console.log('totalArrears: ', totalArrears, typeof totalArrears);
        console.log(
          'defermentAmount: ',
          defermentAmount,
          typeof defermentAmount
        );
        console.log('downPayment: ', downPayment, typeof downPayment);
        console.log('----------------------------------------------');
      }
      newUPB = Number(
        (currentUPB + totalArrears - defermentAmount - downPayment).toFixed(2)
      );
      break;
    case 'SPLIT':
      if (consoleDebug) {
        console.log('NEW UPB----------------------------------------');
        console.log(
          'SPLIT - NewUPB',
          currentUPB + totalArrears - defermentAmount - downPayment
        );
        console.log('currentUPB: ', currentUPB, typeof currentUPB);
        console.log('totalArrears: ', totalArrears, typeof totalArrears);
        console.log(
          'defermentAmount: ',
          defermentAmount,
          typeof defermentAmount
        );
        console.log('downPayment: ', downPayment, typeof downPayment);
        console.log('----------------------------------------------');
      }
      newUPB = Number(
        (currentUPB + totalArrears - defermentAmount - downPayment).toFixed(2)
      );
      break;
    default:
      if (consoleDebug) {
        console.log('NEW UPB---------------------------------------');
        console.log(
          'Forgive/Default - NewUPB',
          currentUPB + totalArrears - downPayment
        );
        console.log('currentUPB: ', currentUPB, typeof currentUPB);
        console.log('totalArrears: ', totalArrears, typeof totalArrears);
        console.log('downPayment: ', downPayment, typeof downPayment);
        console.log('----------------------------------------------');
      }
      newUPB = Number((currentUPB + totalArrears - downPayment).toFixed(2));
      break;
  }
  return newUPB;
};
export default calcNewUPB;

calcNewUPB.propTypes = {
  totalArrears: PropTypes.number.isRequired,
  currentUPB: PropTypes.number.isRequired,
  downPayment: PropTypes.number.isRequired,
  defermentAmount: PropTypes.number.isRequired,
  defermentType: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

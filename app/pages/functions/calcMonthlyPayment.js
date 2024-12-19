const calcMonthlyPayment = (
  currentUPB,
  interestRate,
  term,
  defermentType,
  defermentAmount,
  lastPaidToResolution,
  perDiem,
  downPayment,
  defermentAmount02,
  lateFees,
  legalFees,
  consoleDebug
) => {
  console.log('run calc');
  let formattedInterestRate = Number((interestRate / 100 / 12).toFixed(6));
  let totalInterest =
    downPayment > 0
      ? (lastPaidToResolution + 30) * perDiem
      : lastPaidToResolution * perDiem;

  if (defermentType === 'forgive') {
    totalInterest -= defermentAmount;
  } else if (defermentType === 'split') {
    totalInterest -= defermentAmount02;
  }

  let arrearsLeft = totalInterest + lateFees + legalFees - downPayment;

  let presentValue = currentUPB + arrearsLeft;

  let futureValue = defermentAmount || 0;

  if (defermentType === 'balloon') {
    presentValue -= defermentAmount;
  } else if (defermentType === 'split') {
    presentValue -= defermentAmount02;
  }

  let pvif = Math.pow(1 + formattedInterestRate, term);
  let monthlyPayment =
    (formattedInterestRate * (presentValue * pvif + futureValue)) / (pvif - 1);

  if (consoleDebug) {
    console.log('MONTHLY PAYMENT-------------------------------');
    console.log('currentUPB: ', currentUPB);
    console.log('interestRate: ', interestRate);
    console.log('formattedInterestRate: ', formattedInterestRate);
    console.log('term: ', term);
    console.log('defermentType: ', defermentType);
    if (defermentType === 'split') {
      console.log('deferment (balloon): ', defermentAmount);
      console.log('deferment (forgive): ', defermentAmount02);
    } else {
      console.log('defermentAmount: ', defermentAmount);
    }
    console.log('lastPaidToResolution: ', lastPaidToResolution);
    console.log('perDiem: ', perDiem);
    console.log('downPayment: ', downPayment);
    console.log('Monthly Payment: ', monthlyPayment);
    console.log('Late Fees: ', lateFees);
    console.log('Legal Fees: ', legalFees);
    console.log('----------------------------------------------');
    console.log('totalInterest: ', totalInterest);
    console.log('arrearsLeft: ', arrearsLeft);
    console.log('presentValue: ', presentValue);
    console.log('futureValue: ', futureValue);
    console.log('pvif: ', pvif);
    console.log('----------------------------------------------');
  }
  console.log('return monthly payment: ', monthlyPayment.toFixed(2));
  return Number(monthlyPayment.toFixed(2));
};

export default calcMonthlyPayment;

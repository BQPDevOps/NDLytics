import PropTypes from 'prop-types';
import moment from 'moment';

const calcAccruedInterest = (perDiem, lastPaidToResolution) => {
  if (consoleDebug) {
    console.log('ACCRUED INTEREST---------------------------------');
    console.log('perDiem: ', perDiem);
    console.log('lastPaidToResolution: ', lastPaidToResolution);
    console.log('Accrued Interest: ', perDiem * lastPaidToResolution);
    console.log('----------------------------------------------');
  }
  return Number((perDiem * lastPaidToResolution).toFixed(2));
};

calcAccruedInterest.defaultProps = {
  perDiem: 0,
  lastPaidToResolution: 0,
  consoleDebug: false,
};

calcAccruedInterest.propTypes = {
  perDiem: PropTypes.number.isRequired,
  lastPaidToResolution: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

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

const calcFirstPaymentDueDate = (downPayment, expirationDate, consoleDebug) => {
  if (downPayment === 0) expirationDate;
  if (consoleDebug) {
    console.log('FIRST PAYMENT DUE DATE------------------------');
    console.log(
      'First Payment Due Date: ',
      new Date(moment(expirationDate).add(1, 'months').format('MM/DD/YYYY'))
    );
    console.log('downPayment: ', downPayment);
    console.log('expirationDate: ', expirationDate);
    console.log('----------------------------------------------');
  }
  return new Date(moment(expirationDate).add(1, 'months').format('MM/DD/YYYY'));
};

calcFirstPaymentDueDate.defaultProps = {
  downPayment: 0,
  expirationDate: '',
  consoleDebug: false,
};

calcFirstPaymentDueDate.propTypes = {
  downPayment: PropTypes.number.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

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

const calcLastPaidToResolution = (
  nextDueDate,
  expirationDate,
  lastPaidDate,
  consoleDebug = false
) => {
  const startDate = moment(nextDueDate).isValid()
    ? moment(nextDueDate).subtract(1, 'months').format('YYYY-MM-DD')
    : moment(lastPaidDate).format('YYYY-MM-DD');
  if (consoleDebug) {
    console.log('LAST PAID TO RESOLUTION------------------------');
    console.log(
      'LastPaidToResolution: ',
      calcNumberOfDays(startDate, expirationDate)
    );
    console.log('nextDueDate: ', nextDueDate);
    console.log('expirationDate: ', expirationDate);
    console.log('lastPaidDate: ', lastPaidDate);
    console.log('----------------------------------------------');
  }
  return calcNumberOfDays(startDate, expirationDate);
};

calcLastPaidToResolution.propTypes = {
  nextDueDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  lastPaidDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

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

const calcMonthsDelinquent = (
  nextDueDate,
  expirationDate,
  consoleDebug = false
) => {
  const startDate = moment(
    moment(nextDueDate).subtract(1, 'months').format('YYYY-MM-DD')
  );

  const endDate = moment(moment(expirationDate).format('YYYY-MM-DD'));

  const diffYears = endDate.diff(startDate, 'years');

  startDate.add(diffYears, 'years');

  const diffMonths = endDate.diff(startDate, 'months');

  if (consoleDebug) {
    console.log('MONTH DELINQUENT-------------------------------');
    console.log('Months Delinquent: ', diffYears * 12 + diffMonths);
    console.log('----------------------------------------------');
  }
  return diffYears * 12 + diffMonths;
};

calcMonthsDelinquent.propTypes = {
  nextDueDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

class yearObject {
  constructor(arrears, buySell, finance) {
    this.arrears = arrears;
    this.buySell = buySell;
    this.finance = finance;
  }
  calcTotal = () => {
    return this.arrears + this.buySell + this.finance;
  };
}

const calcNetProfit = (
  notePrice = 0,
  purchaseToResolution = 0,
  totalExpenses = 0,
  downPayment = 0,
  consoleDebug = false
) => {
  const year00 = new yearObject(0, 0, 0);
  const year01 = new yearObject(0, 0, 0);
  const year02 = new yearObject(0, 0, 0);
  const year03 = new yearObject(0, 0, 0);

  year00.buySell = totalExpenses * -1;
  if (purchaseToResolution <= 12) {
    year01.arrears = downPayment;
    year01.buySell = notePrice;
  }

  if (purchaseToResolution > 12 && purchaseToResolution <= 24) {
    year02.arrears = downPayment;
    year02.buySell = notePrice;
  }

  year02.finance = year00.buySell * ((0.16 / 12) * purchaseToResolution);

  if (purchaseToResolution > 24) {
    year03.arrears = downPayment;
  }

  if (purchaseToResolution > 24 && purchaseToResolution <= 36) {
    year03.buySell = notePrice;
  }

  if (consoleDebug) console.log('Year 00: ', year00.calcTotal());
  if (consoleDebug) console.log('Year 01: ', year01.calcTotal());
  if (consoleDebug) console.log('Year 02: ', year02.calcTotal());
  if (consoleDebug) console.log('Year 03: ', year03.calcTotal());
  if (consoleDebug) {
    console.log('NET PROFIT-------------------------------------');
    console.log(
      'NetProfit: ',
      year00.calcTotal() +
        year01.calcTotal() +
        year02.calcTotal() +
        year03.calcTotal()
    );
    console.log('----------------------------------------------');
  }

  return Number(
    (
      year00.calcTotal() +
      year01.calcTotal() +
      year02.calcTotal() +
      year03.calcTotal()
    ).toFixed(2)
  );
};

calcNetProfit.propTypes = {
  notePrice: PropTypes.number.isRequired,
  purchaseToResolution: PropTypes.number.isRequired,
  totalExpenses: PropTypes.number.isRequired,
  downPayment: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

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

calcNewUPB.propTypes = {
  totalArrears: PropTypes.number.isRequired,
  currentUPB: PropTypes.number.isRequired,
  downPayment: PropTypes.number.isRequired,
  defermentAmount: PropTypes.number.isRequired,
  defermentType: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

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

calcNotePrice.propTypes = {
  monthlyPayment: PropTypes.number.isRequired,
  term: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

function calcNumberOfDays(date1, date2, fallbackDate) {
  let start, end;

  // If date1 is empty, use fallbackDate minus 1 month as start date
  if (!date1) {
    start = moment(fallbackDate).subtract(1, 'month');
  } else {
    start = moment(date1);
  }

  end = moment(date2);

  // Calculate difference in days between start and end dates
  const diffInDays = end.diff(start, 'days');

  return diffInDays;
}

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

const calcPurchaseToResolution = (
  purchaseDate,
  expirationDate,
  consoleDebug
) => {
  if (consoleDebug) {
    console.log('PURCHASE TO RESOLUTION--------------------------');
    console.log(
      'Purchase to Resolution: ',
      calcNumberOfDays(purchaseDate, expirationDate)
    );
    console.log('----------------------------------------------');
  }
  return calcNumberOfDays(purchaseDate, expirationDate);
};

calcPurchaseToResolution.defaultProps = {
  purchaseDate: '',
  expirationDate: '',
  consoleDebug: false,
};

calcPurchaseToResolution.propTypes = {
  purchaseDate: PropTypes.string.isRequired,
  expirationDate: PropTypes.string.isRequired,
  consoleDebug: PropTypes.bool,
};

const calcTotalArrears = (
  downPayment,
  lastPaidToResolution,
  perDiem,
  defermentType,
  defermentAmount,
  lateFees,
  legalFees,
  defermentAmount02,
  consoleDebug
) => {
  let totalInterest = 0;

  switch (downPayment > 0) {
    case true:
      totalInterest = (lastPaidToResolution + 30) * perDiem;
    default:
      totalInterest = lastPaidToResolution * perDiem;
  }

  if (defermentType === 'forgive') {
    totalInterest -= defermentAmount;
  }

  if (defermentType === 'split') {
    totalInterest -= defermentAmount02;
  }
  if (consoleDebug) {
    console.log('TOTAL ARREARS---------------------------------');
    console.log('Total Arrears: ', totalInterest + lateFees + legalFees);
    console.log('----------------------------------------------');
  }
  return Number((totalInterest + lateFees + legalFees).toFixed(2));
};

calcTotalArrears.defaultProps = {
  downPayment: 0,
  lastPaidToResolution: 0,
  perDiem: 0,
  defermentType: 'none',
  defermentAmount: 0,
  lateFees: 0,
  legalFees: 0,
  defermentAmount02: 0,
  consoleDebug: false,
};

calcTotalArrears.propTypes = {
  downPayment: PropTypes.number.isRequired,
  lastPaidToResolution: PropTypes.number.isRequired,
  perDiem: PropTypes.number.isRequired,
  defermentType: PropTypes.string.isRequired,
  defermentAmount: PropTypes.number.isRequired,
  lateFees: PropTypes.number.isRequired,
  legalFees: PropTypes.number.isRequired,
  defermentAmount02: PropTypes.number,
  consoleDebug: PropTypes.bool,
};

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

const calcTotalExpenses = (purchasePrice, legalFees, consoleDebug) => {
  if (consoleDebug) {
    console.log('TOTAL EXPENSES----------------------------------');
    console.log('Total Expenses: ', purchasePrice + legalFees + 250);
    console.log('----------------------------------------------');
  }
  return purchasePrice + legalFees + 250;
};
calcTotalExpenses.defaultProps = {
  purchasePrice: 0,
  legalFees: 0,
};
calcTotalExpenses.propTypes = {
  purchasePrice: PropTypes.number.isRequired,
  legalFees: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

const calcUPBPurchaseRatio = (upb = 0, purchasePrice = 0) => {
  return Number((upb / purchasePrice).toFixed(2));
};
calcUPBPurchaseRatio.propTypes = {
  upb: PropTypes.number.isRequired,
  purchasePrice: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

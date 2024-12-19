import PropTypes from 'prop-types';

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
export default calcNetProfit;

calcNetProfit.propTypes = {
  notePrice: PropTypes.number.isRequired,
  purchaseToResolution: PropTypes.number.isRequired,
  totalExpenses: PropTypes.number.isRequired,
  downPayment: PropTypes.number.isRequired,
  consoleDebug: PropTypes.bool,
};

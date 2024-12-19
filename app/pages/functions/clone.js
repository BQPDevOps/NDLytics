import { useEffect, useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import axios from 'axios';

import {
  selectAIEnabled,
  selectInterestRateMin,
  selectInterestRateMax,
  selectAvailableTerms,
} from '../../store/simpleAISlice';
import { SimpleAI } from '../../components/SimpleAI/SimpleAI';

import {
  setLoanData,
  selectLoanData,
  setResolutionData,
  selectResolutionData,
  selectOptions,
  selectInitRedux,
  selectOptionIndex,
  updateOptionIndex,
  updateOptionById,
  addOption,
  removeOption,
  selectSaveRequired,
  updateSaveRequired,
  updatePersistingOptionData,
  setHasDescrpancy,
} from '../../store/appSlice';
import {
  selectRejectDialogOpen,
  updateRejectDialogOpen,
} from '../../store/dialogSlice';

import moment from 'moment';
import {
  Typography,
  Divider,
  Paper,
  Button,
  Box,
  Tabs,
  Radio,
  Tab,
  TextField,
  FormControlLabel,
  RadioGroup,
  Checkbox,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { motion } from 'framer-motion';

import { SimpleDialog } from '../../components/Dialogs';
import RejectForm from '../../forms/RejectForm';
import SimpleCard from '../../components/SimpleCard/SimpleCard';
import { SimpleTextCard, NumberInput } from '../../components';
import FuseUtils from '@fuse/utils/FuseUtils';
import FuseSvgIcon from '@fuse/core/FuseSvgIcon';
import Tasks from '../../components/Tasks/Tasks';

import { handleTabChange } from './actionHandlers';

import calcUPBPurchaseRatio from './calcUPBPurchaseRatio';
import calcPurchaseToResolution from './calcPurchaseToResolution';
import calcLastPaidToResolution from './calcLastPaidToResolution';
import calcMonthsDelinquent from './calcMonthsDelinquent';
import calcAccruedInterest from './calcAccruedInterest';
import calcCLTV from './calcCLTV';
import calcITV from './calcITV';
import calcEquityCoverage from './calcEquityCoverage';
import calcAPY from './calcAPY';
import calcTotalExpenses from './calcTotalExpenses';
import calcTotalDebt from './calcTotalDebt';
import calcTotalArrears from './calcTotalArrears';
import calcFirstPaymentDueDate from './calcFirstPaymentDueDate';
import calcPerDiem from './calcPerDiem';
import calcNetProfit from './calcNetProfit';
import calcNewUPB from './calcNewUPB';
import calcNotePrice from './calcNotePrice';
import calcMonthlyPayment from './calcMonthlyPayment';

const consoleDebug = {
  accruedInterest: false,
  apy: false,
  cltv: false,
  currentOption: false,
  equityCoverage: false,
  firstPaymentDueDate: false,
  itv: false,
  lastPaidToResolution: false,
  modifications: false,
  monthsDelinquent: false,
  netProfit: false,
  newUPB: false,
  notePrice: false,
  perDiem: false,
  purchaseToResolution: false,
  totalArrears: false,
  totalDebt: false,
  totalExpenses: false,
  upbPurchaseRatio: false,
  monthlyPayment: false,
};

function Content() {
  const dispatch = useDispatch();
  const location = useLocation();
  const focusRef = useRef(null);

  const loanData = useSelector(selectLoanData);
  const resolutionData = useSelector(selectResolutionData);
  const options = useSelector(selectOptions);
  const optionIndex = useSelector(selectOptionIndex);
  const initRedux = useSelector(selectInitRedux);
  const saveRequired = useSelector(selectSaveRequired);
  const rejectDialogOpen = useSelector(selectRejectDialogOpen);

  const [initOptionComplete, setInitOptionComplete] = useState(false);
  const [currentOption, setCurrentOption] = useState({});
  const [tabValue, setTabValue] = useState(0);

  const [optionDefermentAmount, setOptionDefermentAmount] = useState(0);
  const [optionDefermentAmount02, setOptionDefermentAmount02] = useState(0);
  const [optionDefermentType, setOptionDefermentType] = useState('none');
  const [optionDownPayment, setOptionDownPayment] = useState(0);
  const [optionHasDeferment, setOptionHasDeferment] = useState(false);
  const [optionMonthlyPayment, setOptionMonthlyPayment] = useState(0);
  const [optionComments, setOptionComments] = useState('');
  const [optionTerm, setOptionTerm] = useState(0);

  const [isSysCurrentUPB, setIsSysCurrentUPB] = useState(true);
  const [isSysPerDiem, setIsSysPerDiem] = useState(true);
  const [isSysPurchasePrice, setIsSysPurchasePrice] = useState(true);
  const [isSysSeniorUPB, setIsSysSeniorUPB] = useState(true);

  const [taskDialogOpen, setTaskDialogOpen] = useState(false);

  const [pastWorkout, setPastWorkout] = useState(0);
  const [accruedInterest, setAccruedInterest] = useState(0);
  const [apy, setAPY] = useState(0);
  const [cltv, setCLTV] = useState(0);
  const [currentUPB, setCurrentUPB] = useState(0);
  const [equityCoverage, setEquityCoverage] = useState(0);
  const [optionInterestRate, setOptionInterestRate] = useState(0);
  const [itv, setITV] = useState(0);
  const [lateFees, setLateFees] = useState(0);
  const [legalFees, setLegalFees] = useState(0);
  const [netProfit, setNetProfit] = useState(0);
  const [newUPB, setNewUPB] = useState(0);
  const [perDiem, setPerDiem] = useState(0);
  const [upbPurchaseRatio, setUPBPurchaseRatio] = useState(0);
  const [purchasePrice, setPurchasePrice] = useState(0);
  const [notePrice, setNotePrice] = useState(0);
  const [totalDebt, setTotalDebt] = useState(0);
  const [totalExpenses, setTotalExpenses] = useState(0);
  const [purchaseToResolution, setPurchaseToResolution] = useState(0);
  const [lastPaidToResolution, setLastPaidToResolution] = useState(0);
  const [monthsDelinquent, setMonthsDelinquent] = useState(0);
  const [originalInterestRate, setOriginalInterestRate] = useState(0);
  const [totalArrears, setTotalArrears] = useState(0);
  const [seniorUPB, setSeniorUPB] = useState(0);
  const [descrepancyValue, setDescrepancyValue] = useState(0);

  const [purchaseDate, setPurchaseDate] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [servicer, setServicer] = useState('');
  const [firstPaymentDueDate, setFirstPaymentDueDate] = useState('');

  const [signedURL, setSignedURL] = useState('');
  const [history, setHistory] = useState([]);
  const [hasHistory, setHasHistory] = useState(false);
  const [hasPayoff, setHasPayoff] = useState(false);

  const openHistoryDialog = () => setTaskDialogOpen(true);
  const closeHistoryDialog = () => setTaskDialogOpen(false);

  const handleSeniorFromRequest = () => {
    setSeniorUPB(resolutionData?.request_senior_upb);
    setIsSysSeniorUPB(!isSysSeniorUPB);
  };
  const handleSeniorFromSystem = () => {
    setSeniorUPB(loanData?.senior_unpaid_principal_balance);
    setIsSysSeniorUPB(!isSysSeniorUPB);
  };

  const handleApplyToLegal = () => {
    setLegalFees((prev) => prev + descrepancyValue);
    setDescrepancyValue(0);
    //dispatch(setHasDescrpancy(false));
  };
  const handleApplyToLate = () => {
    setLateFees((prev) => prev + descrepancyValue);
    setDescrepancyValue(0);
    //dispatch(setHasDescrpancy(false));
  };
  const handleDisregarDescrepancy = () => {
    setDescrepancyValue(0);
    //dispatch(setHasDescrpancy(false));
  };

  const handleCloseRejectDialog = () => {
    dispatch(updateRejectDialogOpen(false));
  };

  const handleSaveOption = () => {
    const currentOption = {
      id: Number(optionIndex),
      optionDefermentAmount: optionDefermentAmount ?? 0,
      optionDefermentType: optionDefermentType ?? 'none',
      optionDownPayment: optionDownPayment ?? 0,
      optionHasDeferment: optionHasDeferment ?? false,
      optionMonthlyPayment: optionMonthlyPayment ?? 0,
      optionInterestRate: optionInterestRate ?? 0,
      optionTerm: optionTerm ?? 0,
      optionComments: optionComments ?? '',
      optionFirstPaymentDueDate: firstPaymentDueDate ?? '',
      optionNewUpb: newUPB ?? 0,
    };
    let exists = undefined;
    options.forEach((option) => {
      if (option.id === currentOption.id) {
        exists = true;
      }
    });
    if (exists) {
      dispatch(
        updateOptionById({ id: currentOption.id, update: currentOption })
      );
    } else {
      dispatch(addOption(currentOption));
    }
    dispatch(updateSaveRequired(false));
  };

  const handleNewOption = () => {
    if (focusRef.current) {
      focusRef.current.focus();
    }
    dispatch(updateOptionIndex(Number(options.length)));

    setOptionTerm(0);
    setOptionDefermentAmount(0);
    setOptionDefermentType('none');
    setOptionHasDeferment(false);
    setOptionDownPayment(0);
    setOptionInterestRate(0);
    setOptionComments('');
    setCurrentOption({ id: Number(options.length) });

    dispatch(updateSaveRequired(true));
  };

  const handleRemoveOption = () => {
    dispatch(removeOption(currentOption.id));
    if (options.length === 1) {
      setCurrentOption(options[0]);
      dispatch(updateOptionIndex(0));
      dispatch(updateSaveRequired(true));
    } else {
      setCurrentOption(options[optionIndex - 1]);
      dispatch(updateOptionIndex(optionIndex - 1));
    }
  };

  const aiEnabled = useSelector(selectAIEnabled);
  const interestRateMin = useSelector(selectInterestRateMin);
  const interestRateMax = useSelector(selectInterestRateMax);
  const availableTerms = useSelector(selectAvailableTerms);

  const simpleAI = new SimpleAI();
  // useEffect(() => {
  //   const run = async () => {
  //     if (!resolutionData) return;

  //     // Check if all required variables are present
  //     if (
  //       aiEnabled !== undefined &&
  //       interestRateMin !== undefined &&
  //       interestRateMax !== undefined &&
  //       availableTerms !== undefined &&
  //       resolutionData.request_payoff_total !== undefined &&
  //       resolutionData.request_monthly_payment !== undefined &&
  //       resolutionData.request_down_payment !== undefined
  //     ) {
  //       console.log('res data:', resolutionData);
  //       const response = await simpleAI.getOptions(
  //         aiEnabled,
  //         interestRateMin,
  //         interestRateMax,
  //         availableTerms,
  //         resolutionData.request_payoff_total,
  //         resolutionData.request_monthly_payment,
  //         resolutionData.request_down_payment
  //       );
  //       return response;
  //     }
  //   };

  //   run().then((res) => {
  //     console.log(res);
  //   });
  // }, [
  //   resolutionData,
  //   aiEnabled,
  //   interestRateMin,
  //   interestRateMax,
  //   availableTerms,
  // ]);

  // useEffect(() => {
  //   if (resolutionData?.request_payoff_late_fees > 0) {
  //     setLateFees(resolutionData?.request_payoff_late_fees);
  //   }
  //   if (resolutionData?.request_payoff_legal_fees > 0) {
  //     setLegalFees(resolutionData?.request_payoff_legal_fees);
  //   }
  // }, []);

  useEffect(() => {
    if (resolutionData?.resolution_history) {
      setHistory(resolutionData?.resolution_history);
      setHasHistory(true);
    } else {
      setHistory([]);
      setHasHistory(false);
    }
  }, [resolutionData?.resolution_history]);

  useEffect(() => {
    async function fetchUrl() {
      const result = await axios.post(
        'https://ipmkbga0h4.execute-api.us-east-1.amazonaws.com/Alpha/synchronous-execution',
        {
          input: {
            execute_action: 'request_signed_url',
            request_payoff_attatchment_id:
              resolutionData?.request_payoff_attatchment_id,
          },
          stateMachineArn:
            'arn:aws:states:us-east-1:450870404863:stateMachine:Synchronous-Executions',
        }
      );
      return result;
    }
    fetchUrl().then((res) => {
      const data = res?.data.output;
      const parsed = JSON.parse(data);
      setSignedURL(parsed?.body.url);
    });
  }, [resolutionData?.request_payoff_attatchment_id]);

  useEffect(() => {
    if (signedURL) {
      setHasPayoff(true);
    }
  }, [signedURL]);

  useEffect(() => {
    const persistentData = {
      perDiem,
      legalFees,
      lateFees,
      accruedInterest,
      pastWorkout,
      purchasePrice,
      purchaseDate,
      currentUPB,
      purchaseToResolution,
      lastPaidToResolution,
      monthsDelinquent,
      upbPurchaseRatio,
    };
    dispatch(updatePersistingOptionData(persistentData));
  }, [
    perDiem,
    legalFees,
    lateFees,
    accruedInterest,
    pastWorkout,
    purchasePrice,
    purchaseDate,
  ]);

  useEffect(() => {
    setCurrentOption(options[optionIndex]);

    setOptionDefermentAmount(options[optionIndex]?.optionDefermentAmount);
    setOptionDefermentType(options[optionIndex]?.optionDefermentType);
    setOptionDownPayment(options[optionIndex]?.optionDownPayment);
    setOptionHasDeferment(options[optionIndex]?.optionHasDeferment);
    setOptionComments(options[optionIndex]?.optionComments);
    setOptionTerm(options[optionIndex]?.optionTerm);
    setOptionInterestRate(options[optionIndex]?.optionInterestRate);
  }, [options, optionIndex]);

  useEffect(() => {
    if (optionTerm !== 0 && optionInterestRate !== 0) {
      const newDescrepancy = (
        Number(resolutionData?.request_payoff_total) - Number(totalDebt)
      ).toFixed(2);
      setDescrepancyValue(Number(newDescrepancy));
      dispatch(setHasDescrpancy(true));
    }
  }, [
    resolutionData,
    totalDebt,
    lateFees,
    legalFees,
    optionTerm,
    optionInterestRate,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const totalArrears = calcTotalArrears(
      optionDownPayment,
      lastPaidToResolution,
      perDiem,
      optionDefermentType,
      optionDefermentAmount,
      lateFees,
      legalFees,
      optionDefermentAmount02,
      consoleDebug.totalArrears
    );
    setTotalArrears(totalArrears);
  }, [
    optionDownPayment,
    lastPaidToResolution,
    perDiem,
    optionDefermentType,
    optionDefermentAmount,
    lateFees,
    legalFees,
    consoleDebug.totalArrears,
    initRedux,
    initOptionComplete,
    optionDefermentAmount02,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const firstPaymentDueDate = calcFirstPaymentDueDate(
      optionDownPayment,
      expirationDate,
      consoleDebug.firstPaymentDueDate
    );

    setFirstPaymentDueDate(firstPaymentDueDate);
  }, [
    optionDownPayment,
    expirationDate,
    consoleDebug.firstPaymentDueDate,
    initRedux,
    initOptionComplete,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const perDiem = calcPerDiem(
      optionInterestRate,
      currentUPB,
      servicer,
      originalInterestRate,
      consoleDebug.perDiem,
      isSysPerDiem
    );
    setPerDiem(perDiem);
  }, [
    optionInterestRate,
    currentUPB,
    servicer,
    originalInterestRate,
    consoleDebug.perDiem,
    isSysPerDiem,
    initRedux,
    initOptionComplete,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const netProfit = calcNetProfit(
      notePrice,
      purchaseToResolution,
      totalExpenses,
      optionDownPayment,
      consoleDebug.netProfit
    );
    setNetProfit(netProfit);
  }, [
    notePrice,
    purchaseToResolution,
    totalExpenses,
    optionDownPayment,
    consoleDebug.netProfit,
    initRedux,
    initOptionComplete,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const newUPB = calcNewUPB(
      totalArrears,
      currentUPB,
      optionDownPayment,
      optionDefermentAmount,
      optionDefermentType,
      optionDefermentAmount02,
      consoleDebug.newUPB
    );
    setNewUPB(newUPB);
  }, [
    totalArrears,
    currentUPB,
    optionDownPayment,
    optionDefermentAmount,
    optionDefermentType,
    consoleDebug.newUPB,
    initRedux,
    initOptionComplete,
    optionDefermentAmount02,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const notePrice = calcNotePrice(
      optionMonthlyPayment,
      optionTerm,
      consoleDebug.notePrice
    );
    setNotePrice(notePrice);
  }, [
    optionMonthlyPayment,
    optionTerm,
    consoleDebug.notePrice,
    initRedux,
    initOptionComplete,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const optionMonthlyPayment = calcMonthlyPayment(
      currentUPB,
      optionInterestRate,
      optionTerm,
      optionDefermentType,
      optionDefermentAmount || 0,
      lastPaidToResolution,
      perDiem,
      optionDownPayment || 0,
      optionDefermentAmount02 || 0,
      lateFees,
      legalFees,
      consoleDebug.monthlyPayment
    );
    setOptionMonthlyPayment(optionMonthlyPayment);
  }, [
    currentUPB,
    optionInterestRate,
    optionTerm,
    optionDefermentType,
    optionDefermentAmount,
    lastPaidToResolution,
    perDiem,
    optionDownPayment,
    legalFees,
    lateFees,
    consoleDebug.monthlyPayment,
    initRedux,
    initOptionComplete,
    optionDefermentAmount02,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const totalDebt = calcTotalDebt(
      accruedInterest,
      legalFees,
      lateFees,
      currentUPB,
      consoleDebug.totalDebt
    );
    setTotalDebt(totalDebt);
  }, [
    initRedux,
    initOptionComplete,
    accruedInterest,
    legalFees,
    lateFees,
    currentUPB,
    consoleDebug.totalDebt,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const totalExpenses = calcTotalExpenses(
      purchasePrice,
      legalFees,
      consoleDebug.totalExpenses
    );
    setTotalExpenses(totalExpenses);
  }, [
    initRedux,
    initOptionComplete,
    purchasePrice,
    legalFees,
    consoleDebug.totalExpenses,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const apy = calcAPY(
      netProfit,
      totalExpenses,
      purchaseToResolution,
      consoleDebug.apy
    );
    setAPY(apy);
  }, [
    initRedux,
    initOptionComplete,
    netProfit,
    totalExpenses,
    purchaseToResolution,
    consoleDebug.apy,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const equityCoverage = calcEquityCoverage(
      seniorUPB,
      loanData?.fair_market_value,
      totalDebt,
      consoleDebug.equityCoverage
    );
    setEquityCoverage(equityCoverage);
  }, [
    initRedux,
    initOptionComplete,
    seniorUPB,
    loanData?.fair_market_value,
    totalDebt,
    consoleDebug.equityCoverage,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const itv = calcITV(
      purchasePrice,
      optionDownPayment,
      loanData?.fair_market_value,
      consoleDebug.itv
    );
    setITV(itv);
  }, [
    initRedux,
    initOptionComplete,
    purchasePrice,
    optionDownPayment,
    loanData?.fair_market_value,
    consoleDebug.itv,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const cltv = calcCLTV(
      seniorUPB,
      totalDebt,
      loanData?.fair_market_value,
      consoleDebug.cltv
    );
    setCLTV(cltv);
  }, [
    initRedux,
    initOptionComplete,
    seniorUPB,
    totalDebt,
    loanData?.fair_market_value,
    consoleDebug.cltv,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const accruedInterest = calcAccruedInterest(
      perDiem,
      lastPaidToResolution,
      consoleDebug.accruedInterest
    );
    setAccruedInterest(accruedInterest);
  }, [
    initRedux,
    initOptionComplete,
    perDiem,
    lastPaidToResolution,
    consoleDebug.accruedInterest,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const monthsDelinquent = calcMonthsDelinquent(
      loanData?.next_due_date,
      resolutionData?.request_payoff_date,
      consoleDebug.monthsDelinquent
    );
    setMonthsDelinquent(monthsDelinquent);
  }, [
    initRedux,
    initOptionComplete,
    loanData?.next_due_date,
    resolutionData?.request_payoff_date,
    consoleDebug.monthsDelinquent,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const upbPurchaseRatio = calcUPBPurchaseRatio(
      currentUPB,
      purchasePrice,
      consoleDebug.upbPurchaseRatio
    );
    setUPBPurchaseRatio(upbPurchaseRatio);
  }, [
    initRedux,
    initOptionComplete,
    currentUPB,
    purchasePrice,
    consoleDebug.upbPurchaseRatio,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const purchaseToResolution = calcPurchaseToResolution(
      loanData?.purchase_date,
      resolutionData?.request_payoff_date,
      consoleDebug.purchaseToResolution
    );
    setPurchaseToResolution(purchaseToResolution);
  }, [
    initRedux,
    initOptionComplete,
    loanData?.purchase_date,
    resolutionData?.request_payoff_date,
    consoleDebug.purchaseToResolution,
  ]);

  useEffect(() => {
    if (initRedux || !initOptionComplete) return;
    const lastPaidToResolution = calcLastPaidToResolution(
      loanData?.next_due_date,
      resolutionData?.request_payoff_date,
      loanData?.last_paid_date,
      consoleDebug.lastPaidToResolution
    );
    setLastPaidToResolution(lastPaidToResolution);
  }, [
    initRedux,
    initOptionComplete,
    loanData?.last_paid_date,
    resolutionData?.request_payoff_date,
    loanData?.next_due_date,
    consoleDebug.lastPaidToResolution,
  ]);

  //----------------------//

  useEffect(() => {
    if (!initRedux && !initOptionComplete) {
      setCurrentUPB(Number(loanData?.unpaid_principal_balance));
      setSeniorUPB(Number(loanData?.senior_unpaid_principal_balance));
      setPurchasePrice(Number(loanData?.purchase_price));
      setPurchaseDate(loanData?.purchase_date);
      setOriginalInterestRate(Number(loanData?.original_interest_rate));
      setServicer(loanData?.servicer);
      setInitOptionComplete(true);
    }
  }, [initOptionComplete, initRedux]);

  useEffect(() => {
    if (!optionHasDeferment) {
      setOptionDefermentType('none');
      setOptionHasDeferment(false);
    }
  }, [optionHasDeferment]);

  useEffect(() => {
    if (initRedux) {
      dispatch(setLoanData(location.state.data.request_loan_number));
      dispatch(setResolutionData(location.state.data));
    }
  }, [initRedux]);

  return (
    <div className='grid grid-cols-5 gap-4'>
      <div className='flex flex-col flex-auto pt-16 pl-16 pr-8'>
        <SimpleDialog
          title='Reject Request'
          description='Create, attach and assign a task in hubspot for this resolution.'
          content={<RejectForm />}
          open={rejectDialogOpen}
          onClose={handleCloseRejectDialog}
        />
        <SimpleDialog
          title='Task History'
          description=''
          content={<Tasks filteredRefs={history} />}
          open={taskDialogOpen}
          onClose={closeHistoryDialog}
        />
        <SimpleTextCard
          title='Borrower'
          text={`${loanData?.borrower_first_name} ${loanData?.borrower_last_name}`}
        />
        <SimpleTextCard title='Property' text={loanData?.property_address} />
        <SimpleTextCard
          title='FMV'
          text={FuseUtils.formatToUSD(loanData?.fair_market_value)}
        />
        <Paper elevation={3} sx={{ mb: 1 }} className='flex flex-col p-16'>
          <Typography className='text-16 font-medium text-gray-800 mb-5'>
            Senior UPB
          </Typography>
          <div className='grid grid-cols-2 w-full'>
            <div className='flex flex-col'>
              <motion.div
                animate={{
                  opacity: isSysSeniorUPB ? 1 : 0,
                }}
                transition={{ duration: 0.5 }}
              >
                <Box
                  sx={{
                    backgroundColor: isSysSeniorUPB
                      ? 'secondary.main'
                      : 'transparent',
                    display: 'flex',
                    flex: 1,
                    p: 0.5,
                    mb: 0.5,
                    opacity: 0.5,
                    borderRadius: '2px',
                  }}
                />
              </motion.div>
              <Button
                onClick={isSysSeniorUPB ? null : handleSeniorFromSystem}
                variant='contained'
                sx={{
                  p: 4,
                  borderRadius: '5px 0px 0px 5px',
                  backgroundColor: isSysSeniorUPB
                    ? 'secondary.main'
                    : 'grey[500]',
                  color: isSysSeniorUPB ? 'white' : 'black',
                  '&:hover': {
                    backgroundColor: isSysSeniorUPB
                      ? 'secondary.main'
                      : 'grey[500]',
                  },
                  '&:disabled': {
                    backgroundColor: isSysSeniorUPB
                      ? 'secondary.main'
                      : 'grey[500]',
                    color: isSysSeniorUPB ? 'white' : 'black',
                  },
                }}
                disabled={isSysSeniorUPB}
              >
                <div className='flex flex-col justify-between'>
                  <Typography className='text-18 font-medium mb-5'>
                    System
                  </Typography>
                  <div className='flex flex-wrap'>
                    <Typography className='text-18 font-medium'>
                      {FuseUtils.formatToUSD(
                        loanData?.senior_unpaid_principal_balance || 0
                      )}
                    </Typography>
                  </div>
                </div>
              </Button>
            </div>
            <div className='flex flex-col'>
              <motion.div
                animate={{
                  opacity: isSysSeniorUPB ? 0 : 1,
                }}
                transition={{ duration: 0.5 }}
              >
                <Box
                  sx={{
                    backgroundColor: isSysSeniorUPB
                      ? 'transparent'
                      : 'secondary.main',
                    display: 'flex',
                    flex: 1,
                    p: 0.5,
                    mb: 0.5,
                    opacity: 0.5,
                    borderRadius: '2px',
                  }}
                />
              </motion.div>
              <Button
                onClick={isSysSeniorUPB ? handleSeniorFromRequest : null}
                variant='contained'
                sx={{
                  p: 4,
                  borderRadius: '0px 5px 5px 0px',
                  backgroundColor: isSysSeniorUPB
                    ? 'grey[500]'
                    : 'secondary.main',
                  color: isSysSeniorUPB ? 'black' : 'white',
                  '&:hover': {
                    backgroundColor: isSysSeniorUPB
                      ? 'grey[500]'
                      : 'secondary.main',
                  },
                  '&:disabled': {
                    backgroundColor: isSysSeniorUPB
                      ? 'grey[500]'
                      : 'secondary.main',
                    color: isSysSeniorUPB ? 'black' : 'white',
                  },
                }}
                disabled={!isSysSeniorUPB}
              >
                <div className='flex flex-col justify-between'>
                  <Typography className='text-18 font-medium mb-5'>
                    Request
                  </Typography>
                  <div className='flex flex-wrap'>
                    <Typography className='text-18 font-medium'>
                      {FuseUtils.formatToUSD(
                        resolutionData?.request_senior_upb || 0
                      )}
                    </Typography>
                  </div>
                </div>
              </Button>
            </div>
          </div>
        </Paper>

        <Paper
          sx={{ mb: 1 }}
          elevation={3}
          className='flex flex-col flex-auto p-16'
        >
          <div className='flex'>
            <Typography className='text-18 font-medium'>
              Payoff Details
            </Typography>
          </div>
          <Divider
            sx={{
              margin: '1.2rem 0',
              background: 'none',
              display: 'block',
            }}
          />
          <div className='flex flex-col gap-4'>
            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Principle Balance
              </Typography>
              <Typography className='text-18 font-medium'>
                {FuseUtils.formatToUSD(
                  resolutionData?.request_payoff_principal
                )}
              </Typography>
            </div>

            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Interest Arrears
              </Typography>
              <Typography className='text-18 font-medium'>
                {FuseUtils.formatToUSD(resolutionData?.request_payoff_interest)}
              </Typography>
            </div>

            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Legal Fees
              </Typography>
              <Typography className='text-18 font-medium'>
                {FuseUtils.formatToUSD(
                  resolutionData?.request_payoff_legal_fees
                )}
              </Typography>
            </div>

            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Late Fees
              </Typography>
              <Typography className='text-18 font-medium'>
                {FuseUtils.formatToUSD(
                  resolutionData?.request_payoff_late_fees
                )}
              </Typography>
            </div>

            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Per Diem
              </Typography>
              <Typography className='text-18 font-medium'>
                {FuseUtils.formatToUSD(resolutionData?.request_payoff_per_diem)}
              </Typography>
            </div>
            <Divider
              sx={{
                margin: '1.2rem 0',
                background: 'none',
                display: 'block',
              }}
            />
            <div className='flex flex-row justify-between'>
              <Typography className='text-18 font-medium text-gray-800'>
                Total Payoff
              </Typography>
              <Box sx={{ border: '1px solid lightgrey', p: 1 }}>
                <Typography className='text-18 font-medium'>
                  {FuseUtils.formatToUSD(resolutionData?.request_payoff_total)}
                </Typography>
              </Box>
            </div>
          </div>
        </Paper>
      </div>
      <div className='flex flex-col flex-auto pt-16 pl-8 pr-8 col-span-2'>
        <Paper
          elevation={3}
          className='flex flex-col flex-auto p-16 gap-10 mb-8'
        >
          <div className='grid grid-cols-1  h-full'>
            <div className='grid grid-cols-4 gap-10'>
              <div className='grid col-start-4'>
                <div className='flex flex-1 justify-end items-center'>
                  <Button
                    disabled={!hasHistory}
                    color='secondary'
                    className='w-1/2'
                    variant='contained'
                    sx={{ borderRadius: '5px', mx: 1 }}
                    onClick={openHistoryDialog}
                  >
                    <FuseSvgIcon size={20}>
                      heroicons-outline:clipboard-check
                    </FuseSvgIcon>{' '}
                    <Typography className='text-12 font-medium mx-5'>
                      History
                    </Typography>
                  </Button>
                </div>
              </div>
            </div>
            <div className='grid grid-cols-3 gap-10 '>
              <div className='grid gap-10'>
                <SimpleCard
                  title='Monthly Payment'
                  value={
                    isNaN(optionMonthlyPayment)
                      ? '$ 0.00'
                      : `${FuseUtils.formatToUSD(optionMonthlyPayment)}`
                  }
                  bgColor={
                    isNaN(optionMonthlyPayment)
                      ? 'white'
                      : 'rgba(0, 230, 0, 0.3)'
                  }
                />

                <SimpleCard
                  title='New UPB'
                  value={
                    isNaN(newUPB)
                      ? '$ 0.00'
                      : `${FuseUtils.formatToUSD(newUPB)}`
                  }
                />

                <SimpleCard
                  title='CLTV'
                  value={isNaN(cltv) ? '% 0.00' : `% ${cltv}`}
                />

                <SimpleCard
                  title='Senior Balance'
                  value={
                    isNaN(seniorUPB)
                      ? '$ 0.00'
                      : `${FuseUtils.formatToUSD(seniorUPB)}`
                  }
                />
              </div>
              <div className='grid gap-10'>
                <SimpleCard
                  title='Down Payment'
                  value={
                    isNaN(optionDownPayment)
                      ? '$ 0.00'
                      : `${FuseUtils.formatToUSD(optionDownPayment)}`
                  }
                />

                <SimpleCard
                  title='Interest Rate'
                  value={
                    isNaN(optionInterestRate)
                      ? '% 0.00'
                      : `% ${optionInterestRate}`
                  }
                />

                <SimpleCard
                  title='ITV'
                  value={isNaN(itv) ? '% 0.00' : `% ${itv}`}
                />

                <SimpleCard
                  title='Equity Coverage'
                  value={
                    isNaN(equityCoverage) ? '% 0.00' : `% ${equityCoverage}`
                  }
                />
              </div>
              <div className='grid gap-10'>
                <SimpleCard
                  title='Term'
                  value={isNaN(optionTerm) ? '0' : `${optionTerm}`}
                />

                <SimpleCard
                  title='Expire Date'
                  value={resolutionData?.request_payoff_date}
                  type='text'
                />

                <SimpleCard
                  title='APY'
                  value={isNaN(apy) ? '% 0.00' : `% ${apy}`}
                />

                <SimpleCard
                  title='Net Profit'
                  value={
                    isNaN(netProfit)
                      ? '$ 0.00'
                      : `${FuseUtils.formatToUSD(netProfit)}`
                  }
                />
              </div>
            </div>

            <Divider className='my-20' />

            <motion.div
              animate={{ y: 0, opacity: 1 }}
              initial={{ y: 50, opacity: 0 }}
              transition={{ duration: 0.5 }}
              className='flex flex-row justify-between items-center px-10'
            >
              <motion.div
                animate={{ y: 0, opacity: 1 }}
                initial={{ y: 50, opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Typography className='text-14 font-medium'>
                  {descrepancyValue !== 0
                    ? `Discrepancy: ${FuseUtils.formatToUSD(descrepancyValue)}`
                    : 'Discrepancy: 0'}
                </Typography>
              </motion.div>
              <div>
                <Button
                  onClick={handleApplyToLegal}
                  variant='contained'
                  sx={{ mx: 0.5 }}
                >
                  Legal Fees
                </Button>
                <Button
                  onClick={handleApplyToLate}
                  variant='contained'
                  sx={{ mx: 0.5 }}
                >
                  Late Fees
                </Button>
                <Button
                  onClick={handleDisregarDescrepancy}
                  variant='contained'
                  sx={{ mx: 0.5 }}
                >
                  Disregard
                </Button>
              </div>
            </motion.div>
            <div className='grid grid-cols-3 gap-10 '>
              <div className='flex flex-col items-center justify-evenly'>
                <NumberInput
                  title='Purchase Price'
                  id='purchase-price'
                  state={
                    isSysPurchasePrice
                      ? Number(loanData?.purchase_price)
                      : purchasePrice
                      ? purchasePrice
                      : 0
                  }
                  setState={(value) => {
                    setPurchasePrice(value);
                    dispatch(updateSaveRequired(true));
                  }}
                  disabled={isSysPurchasePrice}
                  hasSwitch={true}
                  switchState={isSysPurchasePrice || false}
                  switchToggle={() => {
                    setPurchasePrice(0);
                    dispatch(updateSaveRequired(true));
                    setIsSysPurchasePrice(!isSysPurchasePrice);
                  }}
                />
                <div className='flex flex-col'>
                  <div>
                    <Typography>Purchase Date</Typography>
                  </div>
                  <DatePicker
                    value={moment(purchaseDate).utc()}
                    onChange={(value) => {
                      setPurchaseDate(value);
                      dispatch(updateSaveRequired(true));
                    }}
                    slotProps={{
                      textField: { variant: 'outlined', size: 'small' },
                    }}
                  />
                </div>
                <NumberInput
                  title='Current UPB'
                  id={'current-upb'}
                  state={
                    isSysCurrentUPB
                      ? Number(loanData?.unpaid_principal_balance)
                      : currentUPB
                      ? currentUPB
                      : 0
                  }
                  setState={(value) => {
                    setCurrentUPB(value);
                    dispatch(updateSaveRequired(true));
                  }}
                  disabled={isSysCurrentUPB}
                  hasSwitch={true}
                  switchState={isSysCurrentUPB || false}
                  switchToggle={() => {
                    setCurrentUPB(0);
                    dispatch(updateSaveRequired(true));
                    setIsSysCurrentUPB(!isSysCurrentUPB);
                  }}
                />
                <NumberInput
                  title='UPB/Purchase Ratio'
                  id='upb-purchase-ratio'
                  state={upbPurchaseRatio || 0}
                  setState={() => {}}
                  disabled={true}
                  adornment='%'
                />
              </div>
              <div className='flex flex-col items-center justify-evenly'>
                <NumberInput
                  title='Purchase to Resolution'
                  id='purchase-to-resolution'
                  state={purchaseToResolution || 0}
                  setState={() => {}}
                  disabled={true}
                />
                <NumberInput
                  title='Last Paid to Resolution'
                  id='last-paid-to-resolution'
                  state={lastPaidToResolution || 0}
                  setState={() => {}}
                  disabled={true}
                />
                <NumberInput
                  title='Months Delinquent'
                  id='months-delinquent'
                  state={monthsDelinquent || 0}
                  setState={() => {}}
                  disabled={true}
                />
                <NumberInput
                  title='Per Diem'
                  id='per-diem'
                  state={perDiem}
                  setState={(value) => {
                    setPerDiem(value);
                    dispatch(updateSaveRequired(true));
                  }}
                  disabled={isSysPerDiem}
                  hasSwitch={true}
                  switchState={isSysPerDiem || false}
                  switchToggle={() => {
                    setPerDiem(0);
                    setIsSysPerDiem(!isSysPerDiem);
                    dispatch(updateSaveRequired(true));
                  }}
                />
              </div>
              <div className='flex flex-col items-center justify-evenly'>
                <NumberInput
                  title='Legal Fees'
                  id='legal-fees'
                  state={legalFees || 0}
                  setState={(value) => {
                    setLegalFees(value);
                    dispatch(updateSaveRequired(true));
                  }}
                />
                <NumberInput
                  title='Late Fees'
                  id='late-fees'
                  state={lateFees || 0}
                  setState={(value) => {
                    setLateFees(value);
                    dispatch(updateSaveRequired(true));
                  }}
                />
                <NumberInput
                  title='Past Workout'
                  id='past-workout'
                  state={pastWorkout || 0}
                  setState={(value) => {
                    setPastWorkout(value);
                    dispatch(updateSaveRequired(true));
                  }}
                />
                <NumberInput
                  title='Accrued Interest'
                  id='accrued-interest'
                  state={accruedInterest || 0}
                  setState={(value) => {
                    setAccruedInterest(value);
                    dispatch(updateSaveRequired(true));
                  }}
                  disabled={true}
                />
              </div>
            </div>
          </div>
        </Paper>
      </div>
      <div className='flex flex-col flex-auto pt-16 pl-8 pr-16 col-span-2'>
        <Paper
          sx={{ mb: 1 }}
          elevation={3}
          className='flex flex-col flex-auto p-16 gap-4'
        >
          <Tabs
            value={tabValue}
            onChange={(event, value) => handleTabChange(setTabValue, value)}
            indicatorColor='secondary'
            textColor='secondary'
            variant='scrollable'
            scrollButtons='auto'
            classes={{ root: 'w-full h-64 border-b-1' }}
          >
            <Tab label='Option' />
            <Tab label='Payoff' />
          </Tabs>
          {tabValue === 1 && (
            <motion.div
              animate={tabValue !== 1 ? 'hidden' : 'visible'}
              variants={{
                visible: { opacity: 1, height: '100%' },
                hidden: { opacity: 0, height: 0 },
              }}
              transition={{ duration: 0.3 }}
              className={tabValue !== 1 ? 'hidden' : 'visible h-full'}
            >
              {signedURL && (
                <div>
                  <iframe
                    title='payoff'
                    src={`${signedURL}#toolbar=0&navpanes=0`}
                    style={{
                      height: `600px`,
                      width: `650px`,
                    }}
                  />
                </div>
              )}
              {!signedURL && (
                <div className='flex flex-col items-center justify-center h-full'>
                  <Typography variant='h6' color='textSecondary'>
                    No payoff available
                  </Typography>
                </div>
              )}
            </motion.div>
          )}
          {tabValue === 0 && (
            <motion.div
              animate={tabValue !== 0 ? 'hidden' : 'visible'}
              variants={{
                visible: { opacity: 1, height: '100%' },
                hidden: { opacity: 0, height: 0 },
              }}
              transition={{ duration: 0.3 }}
              className={tabValue !== 0 ? 'hidden' : 'visible h-full'}
            >
              <div className='flex flex-1 flex-col gap-4 h-full'>
                <div className='grid grid-cols-2'>
                  <div>
                    <NumberInput
                      title='New Term'
                      id='new-term'
                      state={optionTerm}
                      setState={(value) => {
                        setOptionTerm(value);
                        dispatch(updateSaveRequired(true));
                      }}
                      adornment=''
                      inputRef={focusRef}
                    />
                    <NumberInput
                      title='Down Payment'
                      id='down-payment'
                      state={optionDownPayment}
                      setState={(value) => {
                        setOptionDownPayment(value);
                        dispatch(updateSaveRequired(true));
                      }}
                    />
                    <NumberInput
                      title='Interest Rate'
                      id='interest-rate'
                      state={optionInterestRate}
                      setState={(value) => {
                        setOptionInterestRate(value);
                        dispatch(updateSaveRequired(true));
                      }}
                      adornment='%'
                    />
                  </div>
                  <div className='flex flex-col'>
                    <div className='flex flex-col'>
                      <div>
                        <Typography>Has Deferment</Typography>
                      </div>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={
                              optionHasDeferment ? optionHasDeferment : false
                            }
                            onChange={(e) => {
                              dispatch(updateSaveRequired(true));
                              setOptionHasDeferment(e.target.checked);
                            }}
                          />
                        }
                      />
                    </div>
                    <motion.div
                      animate={optionHasDeferment ? 'visible' : 'hidden'}
                      variants={{
                        visible: { opacity: 1, height: '100%' },
                        hidden: { opacity: 0, height: 0 },
                      }}
                      transition={{ duration: 0.3 }}
                    >
                      {optionHasDeferment ? (
                        <RadioGroup
                          row
                          name='optionDefermentType-radios'
                          value={
                            optionDefermentType ? optionDefermentType : 'none'
                          }
                          onChange={(e) => {
                            dispatch(updateSaveRequired(true));
                            setOptionDefermentType(e.target.value);
                          }}
                        >
                          <FormControlLabel
                            value='balloon'
                            control={<Radio />}
                            label='Balloon'
                          />
                          <FormControlLabel
                            value='forgive'
                            control={<Radio />}
                            label='Forgive'
                          />
                          <FormControlLabel
                            value='split'
                            control={<Radio />}
                            label='Split'
                          />
                        </RadioGroup>
                      ) : null}
                    </motion.div>

                    <div className='flex flex-row'>
                      <motion.div
                        className='mx-5'
                        animate={
                          optionDefermentType !== 'none' ? 'visible' : 'hidden'
                        }
                        variants={{
                          visible: { opacity: 1, height: '100%' },
                          hidden: { opacity: 0, height: 0 },
                        }}
                        transition={{ duration: 0.3 }}
                      >
                        {optionDefermentType ? (
                          <NumberInput
                            title={
                              optionDefermentType !== 'split'
                                ? 'Deferment Amount'
                                : 'Balloon Amount'
                            }
                            id='deferment-amount-01'
                            state={optionDefermentAmount}
                            setState={(value) => {
                              dispatch(updateSaveRequired(true));
                              setOptionDefermentAmount(value);
                            }}
                          />
                        ) : null}
                      </motion.div>
                      <motion.div
                        animate={
                          optionDefermentType === 'split' ? 'visible' : 'hidden'
                        }
                        variants={{
                          visible: { opacity: 1, height: '100%' },
                          hidden: { opacity: 0, height: 0 },
                        }}
                        transition={{ duration: 0.3 }}
                      >
                        {optionDefermentType ? (
                          <NumberInput
                            title='Forgive Amount'
                            id='deferment-amount-02'
                            state={optionDefermentAmount02}
                            setState={(value) => {
                              setOptionDefermentAmount02(value);
                              dispatch(updateSaveRequired(true));
                            }}
                          />
                        ) : null}
                      </motion.div>
                    </div>
                  </div>
                </div>

                <div className='flex flex-1 flex-col'>
                  <div className='flex flex-col flex-1 justify-center items-center py-16'>
                    <TextField
                      sx={{ display: 'flex', height: '100%' }}
                      id='requestComments'
                      label='Comments From Request'
                      type='text'
                      multiline
                      rows={5}
                      variant='outlined'
                      fullWidth
                      value={
                        resolutionData?.request_comments
                          ? resolutionData?.request_comments
                          : ''
                      }
                    />
                    <Divider className='my-20' />
                    <TextField
                      sx={{ display: 'flex', height: '100%' }}
                      id='managerComments'
                      label='Management Comments'
                      type='text'
                      multiline
                      rows={5}
                      variant='outlined'
                      fullWidth
                      value={optionComments}
                      placeholder='Management Comments...'
                      onChange={(e) => {
                        dispatch(updateSaveRequired(true));
                        setOptionComments(e.target.value);
                      }}
                    />
                  </div>
                </div>
                <div className='flex flex-1 flex-col justify-end items-end h-full'>
                  <div className='flex flex-1 flex-row justify-end items-end'>
                    <Button
                      onClick={handleRemoveOption}
                      variant='contained'
                      sx={{ mx: 0.5 }}
                      disabled={saveRequired}
                    >
                      Remove Option
                    </Button>
                    <Button
                      color={saveRequired ? 'success' : 'secondary'}
                      onClick={
                        saveRequired ? handleSaveOption : handleNewOption
                      }
                      variant='contained'
                      sx={{ mx: 0.5 }}
                      disabled={options?.length >= 3}
                    >
                      {saveRequired ? 'Save Option' : 'Add Option'}
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </Paper>
      </div>
    </div>
  );
}
export default Content;

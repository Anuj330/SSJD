import React, { useState } from 'react';
import StatementFilters from './StatementFilters';
import type { Transaction } from '../../types/transaction.types';

const BalanceStatement: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState('2025');
  const [selectedMonth, setSelectedMonth] = useState('October');
  const [selectedDay, setSelectedDay] = useState('3');

  const transactions: Transaction[] = [
    {
      date: '31/08/2025',
      tranxNo: '0',
      shareMoney: { credit: 0, debit: 0, balance: 800 },
      compulsoryDeposit: { credit: 0, debit: 0, balance: 2400 },
      optionalDeposit: { credit: 0, debit: 0, balance: 11 },
      regularLoan: { credit: 0, debit: 0, balance: 0 },
      regularInterest: { credit: 0, debit: 625 },
      emergentLoan: { credit: 0, debit: 0, balance: 0 },
      emergentInterest: { credit: 0, debit: 0 }
    },
    {
      date: '13/08/2025',
      tranxNo: '1861218',
      shareMoney: { credit: 0, debit: 0, balance: 800 },
      compulsoryDeposit: { credit: 300, debit: 0, balance: 2700 },
      optionalDeposit: { credit: 0, debit: 0, balance: 11 },
      regularLoan: { credit: 0, debit: 0, balance: 0 },
      regularInterest: { credit: 0, debit: 0 },
      emergentLoan: { credit: 0, debit: 0, balance: 0 },
      emergentInterest: { credit: 0, debit: 0 }
    },
    {
      date: '08/08/2025',
      tranxNo: '1948511',
      shareMoney: { credit: 8382, debit: 0, balance: 9182 },
      compulsoryDeposit: { credit: 0, debit: 0, balance: 3300 },
      optionalDeposit: { credit: 1618, debit: 0, balance: 1629 },
      regularLoan: { credit: 0, debit: 0, balance: 0 },
      regularInterest: { credit: 0, debit: 0 },
      emergentLoan: { credit: 0, debit: 0, balance: 0 },
      emergentInterest: { credit: 0, debit: 0 }
    },
    {
      date: '08/09/2025',
      tranxNo: '2008552',
      shareMoney: { credit: 0, debit: 0, balance: 10000 },
      compulsoryDeposit: { credit: 0, debit: 0, balance: 4100 },
      optionalDeposit: { credit: 0, debit: 0, balance: 11 },
      regularLoan: { credit: 1250, debit: 0, balance: 48750 },
      regularInterest: { credit: 625, debit: 0 },
      emergentLoan: { credit: 0, debit: 0, balance: 0 },
      emergentInterest: { credit: 0, debit: 0 }
    }
  ];

  const handleDisplay = () => {
    console.log('Fetching data for:', { selectedYear, selectedMonth, selectedDay });
  };

  return (
    <div>
      <StatementFilters
        title="Balance Statement"
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        selectedDay={selectedDay}
        onYearChange={setSelectedYear}
        onMonthChange={setSelectedMonth}
        onDayChange={setSelectedDay}
        onDisplay={handleDisplay}
      />

      <div className="bg-white rounded-xl shadow-lg overflow-x-auto">
        <table className="w-full min-w-max">
          <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Date</th>
              <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Tranx No</th>
              <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap" colSpan={3}>Share Money</th>
              <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap" colSpan={3}>Compulsory Deposit</th>
              <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap" colSpan={3}>Optional Deposit</th>
              <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap" colSpan={3}>Regular Loan</th>
              <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap" colSpan={2}>Regular Interest</th>
            </tr>
            <tr className="bg-blue-500">
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Credit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Debit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Balance</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Credit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Debit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Balance</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Credit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Debit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Balance</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Credit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Debit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Balance</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Credit</th>
              <th className="px-4 py-2 text-xs whitespace-nowrap">Debit</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                <td className="px-4 py-3 text-sm whitespace-nowrap">{txn.date}</td>
                <td className="px-4 py-3 text-sm whitespace-nowrap">{txn.tranxNo}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.shareMoney.credit}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.shareMoney.debit}</td>
                <td className="px-4 py-3 text-sm text-center font-semibold">{txn.shareMoney.balance}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.compulsoryDeposit.credit}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.compulsoryDeposit.debit}</td>
                <td className="px-4 py-3 text-sm text-center font-semibold">{txn.compulsoryDeposit.balance}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.optionalDeposit.credit}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.optionalDeposit.debit}</td>
                <td className="px-4 py-3 text-sm text-center font-semibold">{txn.optionalDeposit.balance}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.regularLoan.credit}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.regularLoan.debit}</td>
                <td className="px-4 py-3 text-sm text-center font-semibold">{txn.regularLoan.balance}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.regularInterest.credit}</td>
                <td className="px-4 py-3 text-sm text-center">{txn.regularInterest.debit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BalanceStatement;
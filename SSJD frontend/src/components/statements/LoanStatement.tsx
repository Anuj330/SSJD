import React, { useState } from 'react';
import StatementFilters from './StatementFilters';
import type { LoanData } from '../../types/loan.types';

const LoanStatement: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState('2025');
  const [selectedMonth, setSelectedMonth] = useState('October');
  const [selectedDay, setSelectedDay] = useState('3');

  const loans: LoanData[] = [
    { id: '1019', type: 'REGULAR LOAN', loanNo: '', balance: 48750, interest: 609 },
    { id: '1020', type: 'EMERGENT LOAN', loanNo: '', balance: 0, interest: 0 },
    { id: '1029', type: 'DAILY DEPOSIT LOAN', loanNo: '', balance: 0, interest: 0 },
    { id: '1030', type: 'HOUSE PROPERTY LOAN', loanNo: '', balance: 0, interest: 0 },
    { id: '1036', type: 'GOLD LOAN', loanNo: '', balance: 0, interest: 0 }
  ];

  const handleDisplay = () => {
    console.log('Fetching loan data for:', { selectedYear, selectedMonth, selectedDay });
  };

  return (
    <div>
      <StatementFilters
        title="Loan Statement"
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        selectedDay={selectedDay}
        onYearChange={setSelectedYear}
        onMonthChange={setSelectedMonth}
        onDayChange={setSelectedDay}
        onDisplay={handleDisplay}
      />

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold">ID</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Loans</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Loan No.</th>
              <th className="px-6 py-4 text-right text-sm font-semibold">Balance</th>
              <th className="px-6 py-4 text-right text-sm font-semibold">Interest</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan, idx) => (
              <tr key={idx} className={`${idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-blue-50 transition`}>
                <td className="px-6 py-4">
                  <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" />
                </td>
                <td className="px-6 py-4 text-sm font-medium text-gray-800">{loan.type}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{loan.loanNo || '-'}</td>
                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-800">
                  ₹{loan.balance.toLocaleString('en-IN')}
                </td>
                <td className="px-6 py-4 text-sm text-right font-semibold text-gray-800">₹{loan.interest}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LoanStatement;
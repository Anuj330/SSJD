export interface LoanData {
  id: string;
  type: string;
  loanNo: string;
  balance: number;
  interest: number;
}

export interface LoanDetail {
  loanId: string;
  loanType: 'REGULAR' | 'EMERGENT' | 'DAILY_DEPOSIT' | 'HOUSE_PROPERTY' | 'GOLD';
  amount: number;
  interestRate: number;
  startDate: string;
  endDate: string;
  status: 'ACTIVE' | 'CLOSED' | 'PENDING';
}
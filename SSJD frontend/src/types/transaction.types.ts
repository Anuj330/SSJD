export interface AccountDetail {
  credit: number;
  debit: number;
  balance: number;
}

export interface Transaction {
  date: string;
  tranxNo: string;
  shareMoney: AccountDetail;
  compulsoryDeposit: AccountDetail;
  optionalDeposit: AccountDetail;
  regularLoan: AccountDetail;
  regularInterest: { credit: number; debit: number };
  emergentLoan: AccountDetail;
  emergentInterest: { credit: number; debit: number };
}
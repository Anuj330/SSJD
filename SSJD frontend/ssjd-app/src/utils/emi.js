// Reducing-balance EMI — mirrors the backend's _generate_emi_schedule formula.
// EMI = P·r·(1+r)^n / ((1+r)^n − 1),  r = annualRate/12/100
export function calcEmi(principal, annualRatePct, months) {
  const P = Number(principal) || 0;
  const n = Math.floor(Number(months) || 0);
  const r = (Number(annualRatePct) || 0) / 100 / 12;
  if (P <= 0 || n <= 0) return { emi: 0, totalInterest: 0, totalPayable: 0, schedule: [] };

  const emi = r > 0 ? (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1) : P / n;

  let balance = P;
  let totalInterest = 0;
  const schedule = [];
  for (let i = 1; i <= n; i++) {
    let interest = balance * r;
    let principalPart = emi - interest;
    if (i === n) principalPart = balance;        // clear residual on last EMI
    if (principalPart > balance) principalPart = balance;
    balance -= principalPart;
    totalInterest += interest;
    schedule.push({
      no: i,
      principal: principalPart,
      interest,
      emi: principalPart + interest,
      balance: Math.max(balance, 0),
    });
  }
  return { emi, totalInterest, totalPayable: P + totalInterest, schedule };
}

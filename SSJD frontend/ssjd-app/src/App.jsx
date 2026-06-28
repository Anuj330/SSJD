import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import MembersList from './pages/members/MembersList';
import MemberDetail from './pages/members/MemberDetail';
import ProfilesList from './pages/profiles/ProfilesList';
import AadhaarMapping from './pages/aadhaar/AadhaarMapping';
import MessagingPage from './pages/messaging/MessagingPage';
import Accounts from './pages/ledger/Accounts';
import JournalEntry from './pages/ledger/JournalEntry';
import TrialBalance from './pages/ledger/TrialBalance';
import Statements from './pages/ledger/Statements';
import SchemesList from './pages/deposits/SchemesList';
import DepositsList from './pages/deposits/DepositsList';
import MemberPassbook from './pages/members/MemberPassbook';
import LoanProducts from './pages/loans/LoanProducts';
import LoansList from './pages/loans/LoansList';
import SharesPage from './pages/shares/SharesPage';
import ReportsPage from './pages/reports/ReportsPage';
import AnalyticsPage from './pages/reports/AnalyticsPage';
import PaymentsPage from './pages/payments/PaymentsPage';
import MyDeposits from './pages/member/MyDeposits';
import MyLoans from './pages/member/MyLoans';
import MyShares from './pages/member/MyShares';

export default function App() {
  return (
    <ErrorBoundary>
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="members" element={<MembersList />} />
        <Route path="members/:id" element={<MemberDetail />} />
        <Route path="members/:id/passbook" element={<MemberPassbook />} />
        <Route path="my-passbook" element={<MemberPassbook />} />
        <Route path="my-deposits" element={<MyDeposits />} />
        <Route path="my-loans" element={<MyLoans />} />
        <Route path="my-shares" element={<MyShares />} />
        <Route path="profiles" element={<ProfilesList />} />
        <Route path="aadhaar" element={<AadhaarMapping />} />
        <Route path="messaging" element={<MessagingPage />} />
        <Route path="schemes" element={<SchemesList />} />
        <Route path="deposits" element={<DepositsList />} />
        <Route path="loan-products" element={<LoanProducts />} />
        <Route path="loans" element={<LoansList />} />
        <Route path="shares" element={<SharesPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="ledger/accounts" element={<Accounts />} />
        <Route path="ledger/journal" element={<JournalEntry />} />
        <Route path="ledger/trial-balance" element={<TrialBalance />} />
        <Route path="ledger/statements" element={<Statements />} />
      </Route>
    </Routes>
    </ErrorBoundary>
  );
}

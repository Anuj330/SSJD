import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Edit, Trash2, Wallet, BookOpen } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import DataTable from '../../components/ui/DataTable';
import { CardSkeleton } from '../../components/ui/Skeleton';
import MemberForm from './MemberForm';
import { useApi } from '../../hooks/useApi';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

export default function MemberDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: member, loading, execute: refresh } = useApi(() => membersService.get(id), [id]);
  const { data: moneyFlow, loading: flowLoading, execute: fetchFlow } = useApi(
    () => membersService.getMoneyFlow(id),
    [id]
  );
  const [showEdit, setShowEdit] = useState(false);

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate this member?')) return;
    try {
      await membersService.deactivate(id);
      toast.success('Member deactivated');
      navigate('/members');
    } catch {
      toast.error('Failed to deactivate');
    }
  };

  const handleEdited = () => {
    setShowEdit(false);
    refresh();
  };

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const flowColumns = [
    { key: 'txn_ref', label: 'Txn Ref' },
    { key: 'txn_type', label: 'Type', render: (v) => <Badge color="blue">{v}</Badge> },
    { key: 'account_name', label: 'Account' },
    {
      key: 'dr_amount',
      label: 'Debit',
      render: (v) => Number(v) > 0 ? <span className="text-amber-600 dark:text-amber-400">{fmt(v)}</span> : '-',
    },
    {
      key: 'cr_amount',
      label: 'Credit',
      render: (v) => Number(v) > 0 ? <span className="text-emerald-600 dark:text-emerald-400">{fmt(v)}</span> : '-',
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '-',
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!member) {
    return (
      <div className="py-16 text-center text-gray-500 dark:text-gray-400">
        Member not found.
        <Button variant="ghost" className="mt-4" onClick={() => navigate('/members')}>
          Back to Members
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/members')}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-3">
              <CardTitle>{member.name}</CardTitle>
              <Badge color={member.is_active ? 'green' : 'red'}>
                {member.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Member ID: {member.id}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate(`/members/${id}/passbook`)}>
              <BookOpen className="h-4 w-4" /> Passbook
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}>
              <Edit className="h-4 w-4" /> Edit
            </Button>
            <Button variant="danger" size="sm" onClick={handleDeactivate}>
              <Trash2 className="h-4 w-4" /> Deactivate
            </Button>
          </div>
        </CardHeader>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
            <p className="text-xs font-medium uppercase text-gray-400">Phone</p>
            <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{member.phone}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
            <p className="text-xs font-medium uppercase text-gray-400">Address</p>
            <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{member.address || 'N/A'}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
            <p className="text-xs font-medium uppercase text-gray-400">Joined</p>
            <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
              {member.created_at ? new Date(member.created_at).toLocaleDateString('en-IN') : 'N/A'}
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center gap-2">
              <Wallet className="h-5 w-5" /> Money Flow
            </div>
          </CardTitle>
          {moneyFlow && (
            <div className="text-right text-sm">
              <span className="text-gray-500 dark:text-gray-400">Net: </span>
              <span className={Number(moneyFlow.net_credit_minus_debit) >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                {fmt(moneyFlow.net_credit_minus_debit)}
              </span>
            </div>
          )}
        </CardHeader>
        <DataTable
          columns={flowColumns}
          data={moneyFlow?.rows ?? []}
          loading={flowLoading}
          emptyMessage="No transactions found for this member"
        />
      </Card>

      <Modal isOpen={showEdit} onClose={() => setShowEdit(false)} title="Edit Member">
        <MemberForm member={member} onSuccess={handleEdited} onCancel={() => setShowEdit(false)} />
      </Modal>
    </div>
  );
}

import { useState } from 'react';
import { Coins, Plus, Minus } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { useApi } from '../../hooks/useApi';
import { useAuthStore } from '../../store/authStore';
import { sharesService } from '../../services/shares';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

export default function SharesPage() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const { data: holdings, loading, execute: refresh } = useApi(() => sharesService.listAll());
  const [showAction, setShowAction] = useState(null); // { type: 'purchase'|'refund' }

  const list = holdings ?? [];
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const columns = [
    { key: 'member_id', label: 'ID' },
    { key: 'member_name', label: 'Member', render: v => <span className="font-medium">{v}</span> },
    { key: 'total_shares', label: 'Shares', render: v => <span className="font-bold">{v}</span> },
    { key: 'face_value_per_share', label: 'Face Value', render: v => fmt(v) },
    { key: 'total_value', label: 'Total Value', render: v => <span className="font-semibold text-emerald-600 dark:text-emerald-400">{fmt(v)}</span> },
  ];

  const totalShares = list.reduce((s, h) => s + h.total_shares, 0);
  const totalValue = list.reduce((s, h) => s + Number(h.total_value), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Share Capital</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Member share holdings — {totalShares} shares worth {fmt(totalValue)}</p>
        </div>
        {isAdmin && <div className="flex gap-2">
          <Button onClick={() => setShowAction({ type: 'purchase' })}><Plus className="h-4 w-4" /> Purchase</Button>
          <Button variant="outline" onClick={() => setShowAction({ type: 'refund' })}><Minus className="h-4 w-4" /> Refund</Button>
        </div>}
      </div>
      <Card>
        {!loading && list.length === 0
          ? <EmptyState icon={Coins} title="No share holdings" description="Members haven't purchased any shares yet." />
          : <DataTable columns={columns} data={list} loading={loading} />}
      </Card>
      {showAction && <Modal isOpen onClose={() => setShowAction(null)} title={showAction.type === 'purchase' ? 'Purchase Shares' : 'Refund Shares'}>
        <ShareActionForm type={showAction.type} onSuccess={() => { setShowAction(null); refresh(); }} onCancel={() => setShowAction(null)} />
      </Modal>}
    </div>
  );
}

function ShareActionForm({ type, onSuccess, onCancel }) {
  const { data: members } = useApi(() => membersService.list());
  const [memberId, setMemberId] = useState('');
  const [shares, setShares] = useState('');
  const [loading, setLoading] = useState(false);
  const memberList = Array.isArray(members) ? members : members?.members ?? [];

  const handleSubmit = async e => {
    e.preventDefault();
    if (!memberId || !shares || Number(shares) <= 0) { toast.error('Fill all fields'); return; }
    setLoading(true);
    try {
      if (type === 'purchase') { await sharesService.purchaseShares(Number(memberId), Number(shares)); toast.success('Shares purchased'); }
      else { await sharesService.refundShares(Number(memberId), Number(shares)); toast.success('Shares refunded'); }
      onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Select label="Member" value={memberId} onChange={e => setMemberId(e.target.value)} options={memberList.map(m => ({ value: String(m.id), label: `${m.name} (#${m.id})` }))} placeholder="Select" />
      <Input label="Number of Shares" type="number" min="1" value={shares} onChange={e => setShares(e.target.value)} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading} variant={type === 'refund' ? 'danger' : 'primary'}>{type === 'purchase' ? 'Purchase' : 'Refund'}</Button>
      </div>
    </form>
  );
}

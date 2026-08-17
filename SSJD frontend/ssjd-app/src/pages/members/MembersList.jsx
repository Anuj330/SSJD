import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Users, RotateCcw } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import MemberForm from './MemberForm';
import { useApi } from '../../hooks/useApi';
import { useDebounce } from '../../hooks/useDebounce';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

export default function MembersList() {
  const [status, setStatus] = useState('active'); // 'active' | 'inactive'
  const { data, loading, execute: refresh } = useApi(() => membersService.list(status), [status]);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const debouncedSearch = useDebounce(search);
  const navigate = useNavigate();

  const members = data?.members ?? [];
  const isInactive = status === 'inactive';

  const filtered = useMemo(() => {
    if (!debouncedSearch) return members;
    const q = debouncedSearch.toLowerCase();
    return members.filter(
      (m) =>
        (m.name || '').toLowerCase().includes(q) ||
        (m.phone || '').toLowerCase().includes(q) ||
        (m.address || '').toLowerCase().includes(q)
    );
  }, [members, debouncedSearch]);

  const handleReactivate = async (id, name) => {
    if (!window.confirm(`Reactivate ${name}?`)) return;
    try {
      await membersService.reactivate(id);
      toast.success('Member reactivated');
      refresh();
    } catch {
      toast.error('Failed to reactivate');
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name', render: (val) => <span className="font-medium">{val}</span> },
    { key: 'phone', label: 'Phone', render: (v) => v || <span className="text-gray-400">—</span> },
    { key: 'address', label: 'Address', render: (v) => v || <span className="text-gray-400">—</span> },
    {
      key: 'is_active',
      label: 'Status',
      render: (val) => <Badge color={val ? 'green' : 'red'}>{val ? 'Active' : 'Deactivated'}</Badge>,
    },
    ...(isInactive
      ? [{
          key: 'actions',
          label: '',
          render: (_v, row) => (
            <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleReactivate(row.id, row.name); }}>
              <RotateCcw className="h-4 w-4" /> Reactivate
            </Button>
          ),
        }]
      : [{
          key: 'created_at',
          label: 'Joined',
          render: (val) => (val ? new Date(val).toLocaleDateString('en-IN') : '-'),
        }]),
  ];

  const handleCreated = () => { setShowForm(false); refresh(); };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Members</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {members.length} {isInactive ? 'deactivated' : 'active'} member{members.length !== 1 ? 's' : ''}
          </p>
        </div>
        {!isInactive && (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4" /> Add Member
          </Button>
        )}
      </div>

      {/* Active / Deactivated tabs */}
      <div className="inline-flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
        {[
          { key: 'active', label: 'Active' },
          { key: 'inactive', label: 'Deactivated' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => { setStatus(t.key); setSearch(''); }}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${
              status === t.key
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        {!loading && members.length === 0 ? (
          <EmptyState
            icon={Users}
            title={isInactive ? 'No deactivated members' : 'No members yet'}
            description={isInactive ? 'Deactivated members will appear here.' : 'Get started by adding your first cooperative member.'}
            action={!isInactive && (
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4" /> Add Member
              </Button>
            )}
          />
        ) : (
          <DataTable
            columns={columns}
            data={filtered}
            loading={loading}
            searchable
            searchValue={search}
            onSearchChange={setSearch}
            onRowClick={(row) => navigate(`/members/${row.id}`)}
          />
        )}
      </Card>

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Add New Member">
        <MemberForm onSuccess={handleCreated} onCancel={() => setShowForm(false)} />
      </Modal>
    </div>
  );
}

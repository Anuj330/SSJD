import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Users } from 'lucide-react';
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

export default function MembersList() {
  const { data, loading, execute: refresh } = useApi(() => membersService.list());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const debouncedSearch = useDebounce(search);
  const navigate = useNavigate();

  const members = data?.members ?? [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return members;
    const q = debouncedSearch.toLowerCase();
    return members.filter(
      (m) => m.name.toLowerCase().includes(q) || m.phone.includes(q) || (m.address || '').toLowerCase().includes(q)
    );
  }, [members, debouncedSearch]);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name', render: (val) => <span className="font-medium">{val}</span> },
    { key: 'phone', label: 'Phone' },
    { key: 'address', label: 'Address' },
    {
      key: 'is_active',
      label: 'Status',
      render: (val) => (
        <Badge color={val ? 'green' : 'red'}>{val ? 'Active' : 'Inactive'}</Badge>
      ),
    },
    {
      key: 'created_at',
      label: 'Joined',
      render: (val) => val ? new Date(val).toLocaleDateString('en-IN') : '-',
    },
  ];

  const handleCreated = () => {
    setShowForm(false);
    refresh();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Members</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {members.length} active member{members.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4" /> Add Member
        </Button>
      </div>

      <Card>
        {!loading && members.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No members yet"
            description="Get started by adding your first cooperative member."
            action={
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4" /> Add Member
              </Button>
            }
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

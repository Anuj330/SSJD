import { useState, useMemo } from 'react';
import { Plus, UserCircle } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import ProfileForm from './ProfileForm';
import { useApi } from '../../hooks/useApi';
import { useDebounce } from '../../hooks/useDebounce';
import { profilesService } from '../../services/profiles';

export default function ProfilesList() {
  const { data: profiles, loading, execute: refresh } = useApi(() => profilesService.list());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editProfile, setEditProfile] = useState(null);
  const debouncedSearch = useDebounce(search);

  const list = Array.isArray(profiles) ? profiles : [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return list;
    const q = debouncedSearch.toLowerCase();
    return list.filter(
      (p) =>
        (p.name || '').toLowerCase().includes(q) ||
        (p.email || '').toLowerCase().includes(q) ||
        (p.phone_number || '').includes(q) ||
        (p.membership_number?.toString() || '').includes(q)
    );
  }, [list, debouncedSearch]);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name', render: (v) => <span className="font-medium">{v || '-'}</span> },
    { key: 'membership_number', label: 'Membership #' },
    { key: 'phone_number', label: 'Phone' },
    { key: 'email', label: 'Email' },
    {
      key: 'gender',
      label: 'Gender',
      render: (v) => v ? <Badge color="purple">{v}</Badge> : '-',
    },
    {
      key: 'date_of_joining',
      label: 'Joined',
      render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '-',
    },
  ];

  const handleSuccess = () => {
    setShowForm(false);
    setEditProfile(null);
    refresh();
  };

  const handleEdit = (profile) => {
    setEditProfile(profile);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Member Profiles</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Detailed member information and documents
          </p>
        </div>
        <Button onClick={() => { setEditProfile(null); setShowForm(true); }}>
          <Plus className="h-4 w-4" /> Add Profile
        </Button>
      </div>

      <Card>
        {!loading && list.length === 0 ? (
          <EmptyState
            icon={UserCircle}
            title="No profiles yet"
            description="Create detailed profiles for cooperative members."
            action={
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4" /> Add Profile
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
            onRowClick={handleEdit}
          />
        )}
      </Card>

      <Modal
        isOpen={showForm}
        onClose={() => { setShowForm(false); setEditProfile(null); }}
        title={editProfile ? 'Edit Profile' : 'Create Profile'}
        size="xl"
      >
        <ProfileForm
          profile={editProfile}
          onSuccess={handleSuccess}
          onCancel={() => { setShowForm(false); setEditProfile(null); }}
        />
      </Modal>
    </div>
  );
}

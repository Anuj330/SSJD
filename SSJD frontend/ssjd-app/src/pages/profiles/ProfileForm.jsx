import { useState } from 'react';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { profilesService } from '../../services/profiles';
import toast from 'react-hot-toast';

const genderOptions = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
];

export default function ProfileForm({ profile, onSuccess, onCancel }) {
  const isEdit = !!profile;
  const [form, setForm] = useState({
    member_id: profile?.member_id || '',
    name: profile?.name || '',
    date_of_birth: profile?.date_of_birth || '',
    gender: profile?.gender || '',
    membership_number: profile?.membership_number || '',
    date_of_joining: profile?.date_of_joining || '',
    address: profile?.address || '',
    email: profile?.email || '',
    phone_number: profile?.phone_number || '',
    aadhar: profile?.aadhar || '',
    pan: profile?.pan || '',
    bank_name: profile?.bank_name || '',
    account_number: profile?.account_number || '',
    ifsc: profile?.ifsc || '',
    nominee1: profile?.nominee1 || '',
    nominee1_dob: profile?.nominee1_dob || '',
    nominee1_relation: profile?.nominee1_relation || '',
    nominee2: profile?.nominee2 || '',
    nominee2_dob: profile?.nominee2_dob || '',
    nominee2_relation: profile?.nominee2_relation || '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!isEdit && !form.member_id) errs.member_id = 'Member ID is required';
    if (form.email && !/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Invalid email';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = {};
      for (const [k, v] of Object.entries(form)) {
        if (v !== '' && v !== null) {
          if (['member_id', 'membership_number', 'account_number'].includes(k)) {
            payload[k] = Number(v);
          } else {
            payload[k] = v;
          }
        }
      }
      if (isEdit) {
        await profilesService.update(profile.id, payload);
        toast.success('Profile updated');
      } else {
        await profilesService.create(payload);
        toast.success('Profile created');
      }
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const Section = ({ title, children }) => (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{title}</h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-6 overflow-y-auto pr-2">
      <Section title="Basic Information">
        {!isEdit && (
          <Input label="Member ID" type="number" value={form.member_id} onChange={set('member_id')} error={errors.member_id} />
        )}
        <Input label="Name" value={form.name} onChange={set('name')} />
        <Input label="Date of Birth" type="date" value={form.date_of_birth} onChange={set('date_of_birth')} />
        <Select label="Gender" value={form.gender} onChange={set('gender')} options={genderOptions} placeholder="Select gender" />
        <Input label="Membership Number" type="number" value={form.membership_number} onChange={set('membership_number')} />
        <Input label="Date of Joining" type="date" value={form.date_of_joining} onChange={set('date_of_joining')} />
      </Section>

      <Section title="Contact Information">
        <Input label="Address" value={form.address} onChange={set('address')} />
        <Input label="Email" type="email" value={form.email} onChange={set('email')} error={errors.email} />
        <Input label="Phone Number" value={form.phone_number} onChange={set('phone_number')} />
      </Section>

      <Section title="Identification">
        <Input label="Aadhar Number" value={form.aadhar} onChange={set('aadhar')} />
        <Input label="PAN Number" value={form.pan} onChange={set('pan')} />
      </Section>

      <Section title="Bank Details">
        <Input label="Bank Name" value={form.bank_name} onChange={set('bank_name')} />
        <Input label="Account Number" value={form.account_number} onChange={set('account_number')} />
        <Input label="IFSC Code" value={form.ifsc} onChange={set('ifsc')} />
      </Section>

      <Section title="Nominee 1">
        <Input label="Name" value={form.nominee1} onChange={set('nominee1')} />
        <Input label="Date of Birth" type="date" value={form.nominee1_dob} onChange={set('nominee1_dob')} />
        <Input label="Relation" value={form.nominee1_relation} onChange={set('nominee1_relation')} />
      </Section>

      <Section title="Nominee 2">
        <Input label="Name" value={form.nominee2} onChange={set('nominee2')} />
        <Input label="Date of Birth" type="date" value={form.nominee2_dob} onChange={set('nominee2_dob')} />
        <Input label="Relation" value={form.nominee2_relation} onChange={set('nominee2_relation')} />
      </Section>

      <div className="sticky bottom-0 flex justify-end gap-3 border-t border-gray-200 bg-white pt-4 dark:border-gray-700 dark:bg-gray-900">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{isEdit ? 'Update' : 'Create'} Profile</Button>
      </div>
    </form>
  );
}

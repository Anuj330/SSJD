import { useState } from 'react';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

export default function MemberForm({ member, onSuccess, onCancel }) {
  const isEdit = !!member;
  const [form, setForm] = useState({
    name: member?.name || '',
    phone: member?.phone || '',
    address: member?.address || '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.phone.trim()) errs.phone = 'Phone is required';
    else if (!/^\d{10}$/.test(form.phone.trim())) errs.phone = 'Phone must be 10 digits';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = { ...form };
      if (!payload.address) delete payload.address;
      if (isEdit) {
        await membersService.update(member.id, payload);
        toast.success('Member updated');
      } else {
        await membersService.create(payload);
        toast.success('Member created');
      }
      onSuccess?.();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Something went wrong';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Full Name"
        placeholder="Enter member name"
        value={form.name}
        onChange={set('name')}
        error={errors.name}
      />
      <Input
        label="Phone Number"
        placeholder="10-digit phone number"
        value={form.phone}
        onChange={set('phone')}
        error={errors.phone}
      />
      <Input
        label="Address"
        placeholder="Enter address (optional)"
        value={form.address}
        onChange={set('address')}
      />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {isEdit ? 'Update' : 'Create'} Member
        </Button>
      </div>
    </form>
  );
}

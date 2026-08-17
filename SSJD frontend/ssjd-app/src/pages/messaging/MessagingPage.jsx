import { useEffect, useState } from 'react';
import { MessageSquare, Send, Phone, Smartphone, Users } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { messagingService } from '../../services/messaging';
import { initials, avatarColor, fmtNum } from '../../utils/format';
import toast from 'react-hot-toast';

const CARD = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow)' };

export default function MessagingPage() {
  const { role } = useAuthStore();
  const [channel, setChannel] = useState('sms');
  const [contacts, setContacts] = useState([]);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState(null); // member id or 'bulk'
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    messagingService.contacts().then(setContacts).catch(() => setContacts([]));
    messagingService.status().then(setStatus).catch(() => setStatus(null));
  }, []);

  if (role !== 'admin') {
    return <div className="p-8 text-center text-sm" style={{ color: 'var(--text-2)' }}>Admins only.</div>;
  }

  const withPhone = contacts.filter((c) => c.has_phone);
  const live = channel === 'sms' ? status?.sms_live : status?.whatsapp_live;
  const providerName = channel === 'sms' ? status?.sms_provider : status?.whatsapp_provider;

  const doSend = async () => {
    if (!message.trim()) return toast.error('Type a message');
    if (!target) return toast.error('Pick a recipient or "All members"');
    setBusy(true);
    try {
      if (target === 'bulk') {
        const r = await messagingService.sendBulk(channel, message.trim());
        toast.success(`${channel.toUpperCase()} sent to ${r.sent}${r.failed ? ` (${r.failed} failed)` : ''}${r.skipped_no_phone ? ` · ${r.skipped_no_phone} had no phone` : ''}`);
      } else {
        const r = await messagingService.send(target, channel, message.trim());
        toast.success(`${channel.toUpperCase()} sent to ${r.to}`);
      }
      setMessage('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Send failed');
    } finally { setBusy(false); }
  };

  const pill = (id, label, Icon) => (
    <button onClick={() => setChannel(id)} className="inline-flex items-center gap-2 rounded-[9px] px-3.5 py-2 text-[13px] font-bold" style={{
      background: channel === id ? 'var(--surface)' : 'transparent',
      color: channel === id ? 'var(--text)' : 'var(--text-2)',
      boxShadow: channel === id ? 'var(--shadow)' : 'none',
    }}><Icon className="h-4 w-4" /> {label}</button>
  );

  return (
    <div className="animate-fade-up space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex gap-[3px] rounded-[11px] p-1" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
          {pill('sms', 'SMS', Smartphone)}
          {pill('whatsapp', 'WhatsApp', MessageSquare)}
        </div>
        <div className="flex-1" />
        <span className="rounded-[7px] px-2.5 py-1 text-[12px] font-bold"
          style={{ color: live ? 'var(--accent)' : 'var(--amber)', background: live ? 'var(--accent-soft)' : 'var(--amber-soft)' }}>
          {live ? `Live · ${providerName}` : 'Test mode (console)'}
        </span>
      </div>

      {!live && (
        <div className="rounded-2xl p-3 text-[13px]" style={{ background: 'var(--blue-soft)', border: '1px solid var(--border)', color: 'var(--blue)' }}>
          No {channel === 'sms' ? 'SMS' : 'WhatsApp'} provider configured — messages are logged to the server (not actually delivered).
          Set the provider env vars to go live.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        {/* Compose */}
        <div style={{ ...CARD, padding: 20 }}>
          <div className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>Compose {channel === 'sms' ? 'SMS' : 'WhatsApp'}</div>
          <div className="mt-1 text-[12.5px]" style={{ color: 'var(--text-2)' }}>
            {target === 'bulk' ? `To: all ${withPhone.length} members with a phone`
              : target ? `To: ${contacts.find((c) => c.id === target)?.name || 'member'}`
              : 'Select a recipient on the right →'}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-[12px]" style={{ color: 'var(--text-2)' }}>
            <span>Insert:</span>
            {['{name}', '{username}', '{acno}'].map((tok) => (
              <button key={tok} type="button" onClick={() => setMessage((m) => m + tok)}
                className="num rounded-md px-2 py-0.5 font-semibold" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--accent)' }}>
                {tok}
              </button>
            ))}
            <span style={{ color: 'var(--text-3)' }}>— filled per member</span>
          </div>
          <textarea
            value={message} onChange={(e) => setMessage(e.target.value)} rows={6}
            placeholder="Hi {name}, your SSJD account ({username})…"
            className="mt-2 w-full rounded-[10px] p-3 text-[13.5px] outline-none"
            style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' }}
          />
          <div className="mt-1 text-right text-[11px]" style={{ color: 'var(--text-3)' }}>{message.length} chars</div>
          <button onClick={doSend} disabled={busy || !target || !message.trim()}
            className="mt-2 inline-flex items-center gap-2 rounded-[10px] px-4 py-2.5 text-[13px] font-bold text-white disabled:opacity-50"
            style={{ background: 'var(--accent)' }}>
            <Send className="h-4 w-4" /> {busy ? 'Sending…' : (target === 'bulk' ? 'Send to all' : 'Send')}
          </button>
        </div>

        {/* Recipients */}
        <div style={{ ...CARD, overflow: 'hidden' }}>
          <button onClick={() => setTarget('bulk')} className="flex w-full items-center gap-3 px-4 py-3 text-left"
            style={{ borderBottom: '1px solid var(--border)', background: target === 'bulk' ? 'var(--accent-soft)' : 'transparent' }}>
            <span className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: 'var(--accent)', color: '#fff' }}><Users className="h-[18px] w-[18px]" /></span>
            <div><div className="text-[13.5px] font-bold" style={{ color: 'var(--text)' }}>All members</div>
              <div className="text-[12px]" style={{ color: 'var(--text-2)' }}>{fmtNum(withPhone.length)} with a phone</div></div>
          </button>
          <div className="max-h-[420px] overflow-y-auto">
            {contacts.map((c) => (
              <button key={c.id} disabled={!c.has_phone} onClick={() => setTarget(c.id)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left disabled:opacity-45"
                style={{ borderBottom: '1px solid var(--border-2)', background: target === c.id ? 'var(--accent-soft)' : 'transparent' }}>
                <span className="flex h-8 w-8 flex-none items-center justify-center rounded-full font-display text-[11px] font-bold text-white" style={{ background: avatarColor(c.name || String(c.id)) }}>{initials(c.name || '?')}</span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13px] font-semibold" style={{ color: 'var(--text)' }}>{c.name}</div>
                  <div className="num flex items-center gap-1 text-[11.5px]" style={{ color: 'var(--text-3)' }}>
                    <Phone className="h-3 w-3" /> {c.phone || 'No phone'}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

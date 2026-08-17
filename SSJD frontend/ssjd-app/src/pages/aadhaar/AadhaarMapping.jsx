import { useEffect, useState, useCallback } from 'react';
import { Upload, ShieldCheck, IdCard, Check, X, Clock, Link2, Unlink, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { aadhaarService } from '../../services/aadhaar';
import { initials, avatarColor } from '../../utils/format';
import toast from 'react-hot-toast';

const CARD = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow)' };
const STATUSES = [
  ['pending', 'Pending'], ['pending_approval', 'Awaiting approval'],
  ['needs_info', 'Needs info'], ['linked', 'Linked'], ['rejected', 'Rejected'],
];
const CONF = {
  high: ['Unique match', 'var(--accent)', 'var(--accent-soft)'],
  ambiguous: ['Duplicate names', 'var(--amber)', 'var(--amber-soft)'],
  fuzzy: ['Near match', 'var(--blue)', 'var(--blue-soft)'],
  none: ['No match', 'var(--debit)', 'var(--debit-soft)'],
};
const STATUS_BADGE = {
  pending: ['var(--text-2)', 'var(--surface-2)'],
  pending_approval: ['var(--amber)', 'var(--amber-soft)'],
  needs_info: ['var(--blue)', 'var(--blue-soft)'],
  linked: ['var(--accent)', 'var(--accent-soft)'],
  rejected: ['var(--debit)', 'var(--debit-soft)'],
};

export default function AadhaarMapping() {
  const { role } = useAuthStore();
  const [filter, setFilter] = useState('pending');
  const [docs, setDocs] = useState([]);
  const [selId, setSelId] = useState(null);

  const loadList = useCallback(async () => {
    try { setDocs((await aadhaarService.list(filter)).documents || []); }
    catch { setDocs([]); }
  }, [filter]);

  useEffect(() => { loadList(); }, [loadList]);

  if (role !== 'admin') {
    return <div className="p-8 text-center text-sm" style={{ color: 'var(--text-2)' }}>Admins only.</div>;
  }

  return (
    <div className="animate-fade-up space-y-5">
      <UploadCard onDone={() => { setFilter('pending'); loadList(); }} />

      <div className="flex flex-wrap gap-2">
        {STATUSES.map(([k, label]) => (
          <button key={k} onClick={() => setFilter(k)} className="rounded-[9px] px-3.5 py-1.5 text-[13px] font-bold"
            style={{ background: filter === k ? 'var(--surface)' : 'transparent', color: filter === k ? 'var(--text)' : 'var(--text-2)', border: '1px solid var(--border)', boxShadow: filter === k ? 'var(--shadow)' : 'none' }}>
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        {/* Queue */}
        <div style={{ ...CARD, overflow: 'hidden' }}>
          <div className="px-4 py-3 text-[13px] font-bold" style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>
            Queue · {docs.length}
          </div>
          <div className="max-h-[560px] overflow-y-auto">
            {docs.length === 0 ? (
              <div className="px-4 py-8 text-center text-[13px]" style={{ color: 'var(--text-3)' }}>Nothing here.</div>
            ) : docs.map((d) => {
              const [fg, bg] = STATUS_BADGE[d.status] || STATUS_BADGE.pending;
              return (
                <button key={d.id} onClick={() => setSelId(d.id)} className="flex w-full items-center gap-3 px-4 py-3 text-left"
                  style={{ borderBottom: '1px solid var(--border-2)', background: selId === d.id ? 'var(--surface-2)' : 'transparent' }}>
                  <IdCard className="h-[18px] w-[18px] flex-none" style={{ color: 'var(--text-3)' }} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13.5px] font-semibold" style={{ color: 'var(--text)' }}>{d.confirmed_name}</div>
                    <div className="num text-[11px]" style={{ color: 'var(--text-3)' }}>XXXX-XXXX-{d.aadhaar_last4 || '????'}</div>
                  </div>
                  <span className="rounded-[6px] px-2 py-0.5 text-[10.5px] font-bold" style={{ color: fg, background: bg }}>{d.status.replace('_', ' ')}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Detail */}
        <div>{selId ? <DetailPanel id={selId} onChange={loadList} /> : (
          <div style={{ ...CARD, padding: 40 }} className="text-center text-[13px]" >
            <span style={{ color: 'var(--text-3)' }}>Select a document from the queue to review.</span>
          </div>
        )}</div>
      </div>
    </div>
  );
}

function UploadCard({ onDone }) {
  const [name, setName] = useState('');
  const [num, setNum] = useState('');
  const [dob, setDob] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!file) return toast.error('Choose an Aadhaar image');
    if (!name.trim()) return toast.error('Enter the name as printed on the card');
    if (num.replace(/\D/g, '').length !== 12) return toast.error('Aadhaar number must be 12 digits');
    setBusy(true);
    try {
      await aadhaarService.upload({ name: name.trim(), aadhaarNumber: num, dob, file });
      toast.success('Uploaded — added to review queue');
      setName(''); setNum(''); setDob(''); setFile(null);
      e.target.reset?.();
      onDone?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally { setBusy(false); }
  };

  const inp = { background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' };
  return (
    <div style={{ ...CARD, padding: 20 }}>
      <div className="mb-1 flex items-center gap-2 text-[15px] font-bold" style={{ color: 'var(--text)' }}>
        <Upload className="h-[18px] w-[18px]" style={{ color: 'var(--accent)' }} /> Upload Aadhaar Card
      </div>
      <p className="mb-4 text-[12.5px]" style={{ color: 'var(--text-2)' }}>
        Confirm the name exactly as printed. The number is masked — only the last 4 digits are stored.
      </p>
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
        <label className="text-[12px] font-semibold sm:col-span-2" style={{ color: 'var(--text-2)' }}>
          Name on card
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="As printed on Aadhaar"
            className="mt-1 w-full rounded-[10px] px-3 py-2.5 text-[13px] outline-none" style={inp} />
        </label>
        <label className="text-[12px] font-semibold" style={{ color: 'var(--text-2)' }}>
          Aadhaar number (12 digits)
          <input value={num} onChange={(e) => setNum(e.target.value)} inputMode="numeric" maxLength={14} placeholder="XXXX XXXX XXXX"
            className="num mt-1 w-full rounded-[10px] px-3 py-2.5 text-[13px] outline-none" style={inp} />
        </label>
        <label className="text-[12px] font-semibold" style={{ color: 'var(--text-2)' }}>
          Date of birth (optional)
          <input type="date" value={dob} onChange={(e) => setDob(e.target.value)}
            className="mt-1 w-full rounded-[10px] px-3 py-2.5 text-[13px] outline-none" style={inp} />
        </label>
        <label className="text-[12px] font-semibold sm:col-span-2" style={{ color: 'var(--text-2)' }}>
          Card image (JPG / PNG / PDF)
          <input type="file" accept="image/*,application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="mt-1 w-full rounded-[10px] px-3 py-2 text-[13px] outline-none" style={inp} />
        </label>
        <div className="sm:col-span-2">
          <button type="submit" disabled={busy} className="rounded-[10px] px-4 py-2.5 text-[13px] font-bold text-white disabled:opacity-50" style={{ background: 'var(--accent)' }}>
            {busy ? 'Uploading…' : 'Upload & find matches'}
          </button>
        </div>
      </form>
    </div>
  );
}

function DetailPanel({ id, onChange }) {
  const [doc, setDoc] = useState(null);
  const [img, setImg] = useState(null);
  const [chosen, setChosen] = useState(null);
  const [basis, setBasis] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const d = await aadhaarService.get(id);
    setDoc(d); setChosen(d.member_id || null); setBasis(d.link_basis || '');
  }, [id]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    let url; aadhaarService.imageObjectUrl(id).then((u) => { url = u; setImg(u); }).catch(() => setImg(null));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [id]);

  if (!doc) return <div style={{ ...CARD, padding: 40 }} className="text-center text-[13px]"><span style={{ color: 'var(--text-3)' }}>Loading…</span></div>;

  const [confLabel, confFg, confBg] = CONF[doc.match_confidence] || CONF.none;
  const act = async (fn, okMsg) => {
    setBusy(true);
    try { await fn(); toast.success(okMsg); await load(); onChange?.(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Action failed'); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-4">
      <div style={{ ...CARD, padding: 18 }}>
        <div className="flex flex-wrap items-start gap-4">
          {img ? <img src={img} alt="Aadhaar" className="h-32 w-52 flex-none rounded-[10px] object-cover" style={{ border: '1px solid var(--border)' }} />
               : <div className="grid h-32 w-52 flex-none place-items-center rounded-[10px] text-[12px]" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text-3)' }}>No image</div>}
          <div className="min-w-0 flex-1">
            <div className="font-display text-[18px] font-bold" style={{ color: 'var(--text)' }}>{doc.confirmed_name}</div>
            <div className="num text-[12.5px]" style={{ color: 'var(--text-2)' }}>Aadhaar XXXX-XXXX-{doc.aadhaar_last4} {doc.dob ? `· DOB ${doc.dob}` : ''}</div>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="rounded-[6px] px-2 py-1 text-[11px] font-bold" style={{ color: confFg, background: confBg }}>{confLabel}</span>
              <span className="rounded-[6px] px-2 py-1 text-[11px] font-bold" style={{ color: (STATUS_BADGE[doc.status] || [])[0], background: (STATUS_BADGE[doc.status] || [])[1] }}>{doc.status.replace('_', ' ')}</span>
            </div>
            {doc.match_confidence === 'ambiguous' && (
              <div className="mt-2 flex items-center gap-1.5 text-[12px]" style={{ color: 'var(--amber)' }}>
                <AlertTriangle className="h-3.5 w-3.5" /> Duplicate names — pick the exact member and state your basis. Needs a second approval.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Linked state */}
      {doc.status === 'linked' && doc.linked_member && (
        <div style={{ ...CARD, padding: 18 }}>
          <div className="flex items-center gap-2 text-[14px] font-bold" style={{ color: 'var(--accent)' }}><ShieldCheck className="h-[18px] w-[18px]" /> Linked to {doc.linked_member.name} (Acc #{doc.linked_member.acno})</div>
          <button disabled={busy} onClick={() => act(() => aadhaarService.unlink(id), 'Unlinked')} className="mt-3 inline-flex items-center gap-1.5 rounded-[9px] px-3 py-2 text-[12.5px] font-bold" style={{ border: '1px solid var(--border)', color: 'var(--debit)' }}>
            <Unlink className="h-4 w-4" /> Unlink
          </button>
        </div>
      )}

      {/* Candidate selection (review states) */}
      {['pending', 'pending_approval', 'needs_info'].includes(doc.status) && (
        <div style={{ ...CARD, overflow: 'hidden' }}>
          <div className="px-5 py-3.5 text-[14px] font-bold" style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>
            Candidate members · {doc.candidates.length}
          </div>
          {doc.candidates.length === 0 ? (
            <div className="px-5 py-8 text-center text-[13px]" style={{ color: 'var(--text-3)' }}>
              No matching member. Defer for more info or reject.
            </div>
          ) : (
            <div className="p-2">
              {doc.candidates.map((c) => (
                <label key={c.member_id} className="flex cursor-pointer items-center gap-3 rounded-[10px] px-3 py-2.5"
                  style={{ background: chosen === c.member_id ? 'var(--accent-soft)' : 'transparent' }}>
                  <input type="radio" name="cand" checked={chosen === c.member_id} onChange={() => setChosen(c.member_id)} style={{ accentColor: 'var(--accent)' }} />
                  <div className="flex h-9 w-9 flex-none items-center justify-center rounded-full font-display text-[12px] font-bold text-white" style={{ background: avatarColor(c.name) }}>{initials(c.name)}</div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13.5px] font-semibold" style={{ color: 'var(--text)' }}>{c.name}</div>
                    <div className="num text-[11.5px]" style={{ color: 'var(--text-2)' }}>
                      Acc #{c.acno} {c.phone ? `· ${c.phone}` : ''} {c.father_name ? `· F: ${c.father_name}` : ''} {c.date_of_joining ? `· joined ${c.date_of_joining}` : ''}
                    </div>
                  </div>
                  <span className="num rounded-[6px] px-2 py-0.5 text-[11px] font-bold" style={{ color: c.score === 100 ? 'var(--accent)' : 'var(--text-2)', background: 'var(--surface-2)' }}>{c.score}%</span>
                </label>
              ))}
            </div>
          )}

          <div className="space-y-3 px-5 pb-5 pt-2">
            <input value={basis} onChange={(e) => setBasis(e.target.value)} placeholder="Basis for the match (e.g. matched on phone / father's name / known in person)"
              className="w-full rounded-[10px] px-3 py-2.5 text-[13px] outline-none" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' }} />
            <div className="flex flex-wrap gap-2">
              {doc.status === 'pending_approval' ? (
                <button disabled={busy} onClick={() => act(() => aadhaarService.approve(id), 'Approved & linked')} className="inline-flex items-center gap-1.5 rounded-[9px] px-4 py-2.5 text-[13px] font-bold text-white" style={{ background: 'var(--accent)' }}>
                  <Check className="h-4 w-4" /> Approve link
                </button>
              ) : (
                <button disabled={busy || !chosen} onClick={() => act(() => aadhaarService.link(id, chosen, basis), 'Link recorded')} className="inline-flex items-center gap-1.5 rounded-[9px] px-4 py-2.5 text-[13px] font-bold text-white disabled:opacity-50" style={{ background: 'var(--accent)' }}>
                  <Link2 className="h-4 w-4" /> Link to selected member
                </button>
              )}
              <button disabled={busy} onClick={() => act(() => aadhaarService.defer(id, basis), 'Deferred')} className="inline-flex items-center gap-1.5 rounded-[9px] px-3.5 py-2.5 text-[13px] font-bold" style={{ border: '1px solid var(--border)', color: 'var(--blue)' }}>
                <Clock className="h-4 w-4" /> Defer
              </button>
              <button disabled={busy} onClick={() => act(() => aadhaarService.reject(id, basis), 'Rejected')} className="inline-flex items-center gap-1.5 rounded-[9px] px-3.5 py-2.5 text-[13px] font-bold" style={{ border: '1px solid var(--border)', color: 'var(--debit)' }}>
                <X className="h-4 w-4" /> Reject
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Audit trail */}
      <div style={{ ...CARD, overflow: 'hidden' }}>
        <div className="px-5 py-3.5 text-[14px] font-bold" style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>Audit trail</div>
        <div className="p-3">
          {doc.audit.map((a, i) => (
            <div key={i} className="flex gap-3 px-2 py-1.5 text-[12.5px]">
              <span className="num flex-none" style={{ color: 'var(--text-3)' }}>{a.at?.slice(0, 16).replace('T', ' ')}</span>
              <span className="font-semibold" style={{ color: 'var(--text)' }}>{a.action}</span>
              <span className="min-w-0 flex-1 truncate" style={{ color: 'var(--text-2)' }}>{a.detail}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

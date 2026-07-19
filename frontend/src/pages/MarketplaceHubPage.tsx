import React, { useEffect, useMemo, useState } from 'react';
import {
  Download,
  Package,
  Plus,
  RefreshCw,
  Star,
  TrendingUp,
  X,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import {
  fetchMarketplaceListing,
  fetchMarketplaceListings,
  fetchMarketplaceRatings,
  fetchMarketplaceSummary,
  installMarketplaceListing,
  MarketplaceListing,
  MarketplaceRating,
  MarketplaceSummary,
  publishMarketplaceListing,
  rateMarketplaceListing,
} from '../data/api';

type SortMode = 'featured' | 'popular' | 'top_rated';

const StarRow: React.FC<{ value: number; size?: 'sm' | 'md' }> = ({ value, size = 'sm' }) => {
  const cls = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} className={`${cls} ${n <= Math.round(value) ? 'text-amber-400 fill-amber-400' : 'text-gray-700'}`} />
      ))}
    </div>
  );
};

export const MarketplaceHubPage: React.FC = () => {
  const { showToast } = useApp();
  const [listings, setListings] = useState<MarketplaceListing[] | null>(null);
  const [summary, setSummary] = useState<MarketplaceSummary | null>(null);
  const [sort, setSort] = useState<SortMode>('featured');
  const [kindFilter, setKindFilter] = useState<string>('');
  const [selectedId, setSelectedId] = useState('');
  const [selected, setSelected] = useState<MarketplaceListing | null>(null);
  const [ratings, setRatings] = useState<MarketplaceRating[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [reviewText, setReviewText] = useState('');
  const [reviewStars, setReviewStars] = useState(5);
  const [showPublish, setShowPublish] = useState(false);
  const [publishName, setPublishName] = useState('');
  const [publishSummary, setPublishSummary] = useState('');
  const [publishKind, setPublishKind] = useState('agent');

  const refreshListings = async (nextSort = sort, nextKind = kindFilter) => {
    const data = await fetchMarketplaceListings(nextKind || undefined, nextSort);
    setListings(data);
    if (data && data.length && !data.some((l) => l.listingId === selectedId)) {
      setSelectedId(data[0].listingId);
    }
  };

  const refreshAll = async () => {
    await Promise.all([refreshListings(), fetchMarketplaceSummary().then(setSummary)]);
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshListings(sort, kindFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, kindFilter]);

  useEffect(() => {
    if (!selectedId) return;
    Promise.all([fetchMarketplaceListing(selectedId), fetchMarketplaceRatings(selectedId)]).then(([listing, r]) => {
      setSelected(listing);
      setRatings(r);
    });
  }, [selectedId]);

  const handleInstall = async (listingId: string) => {
    setBusy(true);
    try {
      const ok = await installMarketplaceListing(listingId);
      if (!ok) {
        showToast('Install failed', 'warning');
        return;
      }
      showToast('Installed — real agent/workflow created.', 'success');
      await refreshAll();
      if (listingId === selectedId) setSelected(await fetchMarketplaceListing(listingId));
    } finally {
      setBusy(false);
    }
  };

  const handleRate = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await rateMarketplaceListing(selected.listingId, reviewStars, reviewText);
      if (!updated) {
        showToast('Rating failed', 'warning');
        return;
      }
      setSelected(updated);
      setRatings(await fetchMarketplaceRatings(selected.listingId));
      setReviewText('');
      showToast('Rating submitted.', 'success');
      await refreshListings();
    } finally {
      setBusy(false);
    }
  };

  const handlePublish = async () => {
    if (!publishName.trim()) return;
    setBusy(true);
    try {
      const created = await publishMarketplaceListing(publishKind, publishName.trim(), publishSummary.trim(), 'local');
      if (!created) {
        showToast('Publish failed', 'warning');
        return;
      }
      setShowPublish(false);
      setPublishName('');
      setPublishSummary('');
      showToast('Listing published.', 'success');
      await refreshAll();
      setSelectedId(created.listingId);
    } finally {
      setBusy(false);
    }
  };

  const kinds = useMemo(() => summary?.kinds || [], [summary]);

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-[#171524] via-[#14141c] to-[#101018] p-6 sm:p-8 shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase tracking-wider">
                v160 Agent Marketplace
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Marketplace Hub</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Browse, install, and rate local agent and workflow bundles. Installing creates a real agent profile or workflow definition — no external network calls.
            </p>
          </div>
          <div className="flex gap-2 self-start lg:self-auto">
            <button
              onClick={() => setShowPublish(true)}
              className="px-4 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 text-xs font-bold flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Publish
            </button>
            <button
              onClick={refreshAll}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-200 flex items-center justify-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Total listings</div>
          <div className="text-2xl font-extrabold text-white">{summary?.totalListings ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Total installs</div>
          <div className="text-2xl font-extrabold text-white">{summary?.totalInstalls ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Total ratings</div>
          <div className="text-2xl font-extrabold text-white">{summary?.totalRatings ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Kinds</div>
          <div className="text-xs font-mono text-gray-300 mt-1.5">
            {Object.entries(summary?.listingsByKind || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || '—'}
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GlassCard className="space-y-0" padding="none">
            <div className="flex flex-wrap items-center gap-2 p-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5 mr-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-white">Sort</span>
              </div>
              {(['featured', 'popular', 'top_rated'] as SortMode[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setSort(s)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-mono transition-colors ${
                    sort === s ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'bg-white/[0.03] text-gray-400 border border-white/[0.06] hover:border-white/20'
                  }`}
                >
                  {s.replace('_', ' ')}
                </button>
              ))}
              <div className="flex-1" />
              <select
                value={kindFilter}
                onChange={(e) => setKindFilter(e.target.value)}
                className="px-2 py-1.5 rounded-lg bg-black/30 border border-white/10 text-[11px] text-gray-300 font-mono"
              >
                <option value="">All kinds</option>
                {kinds.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
            </div>
            <div className="max-h-[600px] overflow-y-auto divide-y divide-white/[0.05]">
              {!listings ? (
                <div className="p-8 text-center text-xs text-gray-500 font-mono">Loading listings...</div>
              ) : listings.length === 0 ? (
                <div className="p-8 text-center text-xs text-gray-500 font-mono">No listings match this filter.</div>
              ) : listings.map((l) => (
                <button
                  key={l.listingId}
                  onClick={() => setSelectedId(l.listingId)}
                  className={`w-full text-left p-4 transition-colors ${l.listingId === selectedId ? 'bg-cyan-500/10' : 'hover:bg-white/[0.02]'}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-400 uppercase">{l.kind}</span>
                        {l.isFeatured && <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">Featured</span>}
                        <span className="text-sm font-bold text-white truncate">{l.name}</span>
                      </div>
                      <p className="text-[11px] text-gray-500 truncate">{l.summary}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <StarRow value={l.averageRating} />
                      <span className="text-[10px] font-mono text-gray-500">{l.installs} installs</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>
        </div>

        <div className="space-y-4">
          {selected ? (
            <>
              <GlassCard className="space-y-3">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-sm font-bold text-white truncate">{selected.name}</h2>
                </div>
                <p className="text-xs text-gray-400">{selected.summary}</p>
                <div className="flex items-center gap-2">
                  <StarRow value={selected.averageRating} size="md" />
                  <span className="text-[11px] font-mono text-gray-500">
                    {selected.averageRating.toFixed(1)} ({selected.ratingCount})
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Publisher</div>
                    <div className="text-white truncate">{selected.publisher}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Installs</div>
                    <div className="text-white">{selected.installs}</div>
                  </div>
                </div>
                <button
                  onClick={() => handleInstall(selected.listingId)}
                  disabled={busy}
                  className="w-full px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  Install ({selected.kind === 'agent' ? 'creates agent profile' : 'creates workflow'})
                </button>
              </GlassCard>

              <GlassCard className="space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Rate this listing</h3>
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button key={n} onClick={() => setReviewStars(n)}>
                      <Star className={`w-5 h-5 ${n <= reviewStars ? 'text-amber-400 fill-amber-400' : 'text-gray-700'}`} />
                    </button>
                  ))}
                </div>
                <textarea
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  placeholder="Optional review..."
                  className="w-full min-h-[60px] rounded-xl bg-black/40 border border-white/10 p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                />
                <button
                  onClick={handleRate}
                  disabled={busy}
                  className="w-full px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-200 font-bold text-xs transition-colors disabled:opacity-50"
                >
                  Submit rating
                </button>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {(ratings || []).map((r) => (
                    <div key={r.ratingId} className="p-2 rounded-lg bg-black/20 border border-white/[0.05]">
                      <StarRow value={r.rating} />
                      {r.review && <p className="text-[11px] text-gray-400 mt-1">{r.review}</p>}
                    </div>
                  ))}
                  {ratings && ratings.length === 0 && (
                    <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No ratings yet.</div>
                  )}
                </div>
              </GlassCard>
            </>
          ) : (
            <GlassCard><div className="py-12 text-center text-xs text-gray-500">Select a listing to inspect.</div></GlassCard>
          )}
        </div>
      </div>

      {showPublish && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <GlassCard className="w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">Publish a listing</h3>
              <button onClick={() => setShowPublish(false)}><X className="w-4 h-4 text-gray-400" /></button>
            </div>
            <select
              value={publishKind}
              onChange={(e) => setPublishKind(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white"
            >
              <option value="agent">Agent</option>
              <option value="workflow">Workflow</option>
            </select>
            <input
              value={publishName}
              onChange={(e) => setPublishName(e.target.value)}
              placeholder="Listing name"
              className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
            />
            <textarea
              value={publishSummary}
              onChange={(e) => setPublishSummary(e.target.value)}
              placeholder="Short summary"
              className="w-full min-h-[70px] rounded-xl bg-black/40 border border-white/10 p-3 text-xs text-white placeholder-gray-500"
            />
            <button
              onClick={handlePublish}
              disabled={busy || !publishName.trim()}
              className="w-full px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-white font-bold text-xs transition-colors disabled:opacity-50"
            >
              Publish
            </button>
          </GlassCard>
        </div>
      )}
    </div>
  );
};

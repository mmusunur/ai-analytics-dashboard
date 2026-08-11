import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || '';

export default function WarehouseSalesAnalytics({ globalDate, globalTargetDb = 'pg_dev', externalFilters, copilotFilterActive }) {
  const [summary, setSummary] = useState(null);
  const [items, setItems] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  // Strict date behavior: tracks when selected date has genuinely no data
  const [noDataForDate, setNoDataForDate] = useState(false);

  // Table Level Filter Parameters
  const [filterWhs, setFilterWhs] = useState('');
  const [filterBatchId, setFilterBatchId] = useState('');
  const [filterInvoice, setFilterInvoice] = useState('');
  const [filterOnlyScratches, setFilterOnlyScratches] = useState(false);

  // Handle external filter requests from Copilot or Anomaly panel
  useEffect(() => {
    if (externalFilters) {
      const rawW = externalFilters.whse || externalFilters.oewhse || externalFilters.whs_num || '';
      setFilterWhs(rawW ? String(rawW).trim() : '');
      setFilterBatchId(externalFilters.batch !== undefined ? externalFilters.batch : '');
      setFilterInvoice(externalFilters.invoice !== undefined ? externalFilters.invoice : '');
      setFilterOnlyScratches(Boolean(externalFilters.onlyScratches));
    } else {
      setFilterWhs('');
      setFilterBatchId('');
      setFilterInvoice('');
      setFilterOnlyScratches(false);
    }
  }, [externalFilters]);

  const LIMIT = 20;
  // ✅ TASK 19 & Copilot Mandate: When Copilot mode is active, date filter is DISABLED (oerdte="")
  // so the table queries the full dataset across all dates for the prompted parameters.
  const isCopilotMode = copilotFilterActive || Boolean(externalFilters?.whse || externalFilters?.batch || externalFilters?.invoice || externalFilters?.onlyScratches);
  const oerdte = isCopilotMode ? '' : (globalDate ? globalDate.replace(/-/g, '') : '');

  // Reset & initial load on DB target, date change, or filter inputs
  useEffect(() => {
    let isSubscribed = true;
    const fetchInitial = async () => {
      setLoading(true);
      setNoDataForDate(false);
      try {
        const scratchParam = filterOnlyScratches ? '&only_scratches=true' : '';
        const res = await axios.get(`${API}/api/warehouse/statistics?target_db=${globalTargetDb}&oerdte=${oerdte}&batch_id=${filterBatchId}&oewhse=${filterWhs}&oeinv=${filterInvoice}${scratchParam}&limit=${LIMIT}&offset=0`);
        if (!isSubscribed) return;

        let fetchedItems = res.data?.warehouse_items || [];
        const totalFromServer = res.data.total_count ?? fetchedItems.length;

        // ✅ STRICT DATE BEHAVIOR: If a specific date was chosen and zero records
        // were returned, flag it so we show a clear empty state — no silent fallback.
        if (oerdte && totalFromServer === 0) {
          setNoDataForDate(true);
          setItems([]);
          setTotalCount(0);
          setSummary(null);
          setHasMore(false);
          return;
        }

        if (filterWhs) {
          const targetClean = String(filterWhs).trim().replace(/^0+/, '');
          fetchedItems = fetchedItems.filter(it => String(it.whs_num).trim().replace(/^0+/, '') === targetClean);
        }
        if (filterBatchId) {
          fetchedItems = fetchedItems.filter(it => String(it.batch_id).trim().includes(String(filterBatchId).trim()));
        }
        if (filterInvoice) {
          fetchedItems = fetchedItems.filter(it => String(it.invc_num_stg).trim().includes(String(filterInvoice).trim()));
        }
        if (filterOnlyScratches) {
          fetchedItems = fetchedItems.filter(it => (it.whs_scrtch_qty_stg || 0) > 0);
        }

        setSummary(res.data.summary || null);
        setItems(fetchedItems);
        setTotalCount(totalFromServer);
        setHasMore(res.data.has_more ?? false);
      } catch (err) {
        if (!isSubscribed) return;
        console.error('[WarehouseSalesAnalytics] API query error:', err);
        setItems([]);
        setTotalCount(0);
        setSummary(null);
      } finally {
        if (isSubscribed) setLoading(false);
      }
    };
    fetchInitial();
    return () => { isSubscribed = false; };
  }, [globalTargetDb, oerdte, filterWhs, filterBatchId, filterInvoice, filterOnlyScratches]);

  // Load next batch on scroll down
  const loadMoreData = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextOffset = items.length;
    try {
      const res = await axios.get(`${API}/api/warehouse/statistics?target_db=${globalTargetDb}&oerdte=${oerdte}&batch_id=${filterBatchId}&oewhse=${filterWhs}&oeinv=${filterInvoice}&limit=${LIMIT}&offset=${nextOffset}`);
      setItems((prev) => [...prev, ...(res.data.warehouse_items || [])]);
      setHasMore(res.data.has_more ?? false);
    } catch (err) {
      console.error('Failed to fetch next batch of warehouse data:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollHeight - scrollTop - clientHeight < 50) {
      loadMoreData();
    }
  };

  // Format oerdte for display: 20260728 → 2026-07-28
  const displayDate = oerdte && oerdte.length === 8
    ? `${oerdte.slice(0,4)}-${oerdte.slice(4,6)}-${oerdte.slice(6,8)}`
    : oerdte || 'selected date';

  return (
    <div className="card" id="warehouse-table-card" style={{ marginTop: '24px', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Warehouse & Invoice Sales Analytics
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
            Identifies sales information for warehouse item level and invoice level transfer to Procurement systems.
          </p>
        </div>

        {/* Dynamic Parameter Filter Bar: Warehouse (oewhse), Batch ID (batch_id), Invoice (oeinv) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>Warehouse (oewhse):</span>
            <select
              value={filterWhs}
              onChange={(e) => setFilterWhs(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600
              }}
            >
              <option value="">All Warehouses</option>
              {(() => {
                const fromTotals = (summary?.warehouse_totals || [])
                  .map(w => String(w.whs_num ?? w.warehouse ?? '').trim())
                  .filter(Boolean);
                const fromItems = items.map(it => String(it.whs_num ?? '').trim()).filter(Boolean);
                const optionsSet = new Set([...fromTotals, ...fromItems]);
                if (filterWhs) optionsSet.add(String(filterWhs).trim());
                const sortedWhs = Array.from(optionsSet).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
                return sortedWhs.map(w => (
                  <option key={w} value={w}>Whse {w}</option>
                ));
              })()}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>Batch ID (batch_id):</span>
            <input
              type="text"
              placeholder="e.g. 1851"
              value={filterBatchId}
              onChange={(e) => setFilterBatchId(e.target.value)}
              style={{
                width: '90px',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>Invoice # (oeinv):</span>
            <input
              type="text"
              placeholder="e.g. 487613"
              value={filterInvoice}
              onChange={(e) => setFilterInvoice(e.target.value)}
              style={{
                width: '100px',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600
              }}
            />
          </div>

          <button
            type="button"
            onClick={() => setFilterOnlyScratches(!filterOnlyScratches)}
            style={{
              background: filterOnlyScratches ? 'rgba(239, 68, 68, 0.25)' : 'var(--bg-secondary)',
              color: filterOnlyScratches ? '#fca5a5' : 'var(--text-secondary)',
              border: filterOnlyScratches ? '1px solid rgba(239, 68, 68, 0.6)' : '1px solid var(--border-color)',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.2s ease'
            }}
          >
            🔴 {filterOnlyScratches ? 'Scratch Items Only ✓' : 'Filter Scratches'}
          </button>

          <span style={{
            fontSize: '12px',
            color: '#34D399',
            background: 'rgba(52, 211, 153, 0.1)',
            border: '1px solid rgba(52, 211, 153, 0.2)',
            padding: '4px 10px',
            borderRadius: '6px',
            fontWeight: 700
          }}>
            Target DB: {globalTargetDb.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '20px' }}>
          <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Total Cases Built (cases_bld_stg)</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-primary)', marginTop: '4px' }}>
              {(summary.total_cases_built ?? 0).toLocaleString()}
            </div>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Original Order Qty (orgnl_ordr_qty)</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: '#34d399', marginTop: '4px' }}>
              {(summary.total_original_order_qty ?? 0).toLocaleString()}
            </div>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Invoices Processed</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: '#c084fc', marginTop: '4px' }}>
              {summary.total_invoices_processed ?? 0}
            </div>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Procurement Transfer Rate</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: '#f59e0b', marginTop: '4px' }}>
              {summary.procurement_fulfillment_rate ?? '0%'}
            </div>
          </div>
        </div>
      )}

      {/* No-data empty state — shown when selected date has zero records */}
      {noDataForDate && !loading && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          padding: '48px 24px', borderRadius: '10px', marginBottom: '12px',
          background: 'rgba(124, 58, 237, 0.06)',
          border: '1px dashed rgba(124, 58, 237, 0.35)'
        }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>📭</div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Data Available for {displayDate}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '440px' }}>
            The selected order date <strong style={{ color: '#a78bfa' }}>{displayDate}</strong> has no records
            in <strong style={{ color: '#34d399' }}>{globalTargetDb.toUpperCase()}</strong>.
            Please select a different date that has data, or clear the date filter to view all available records.
          </div>
          <div style={{ marginTop: '16px', fontSize: '12px', color: '#6b7280' }}>
            💡 Tip: The AI Data Copilot above always queries the full dataset regardless of date.
          </div>
        </div>
      )}

      {/* Row Count Badge & Query Status — only when we have data */}
      {!noDataForDate && (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Data Table Rows: <span style={{ color: 'var(--color-primary-light)', fontWeight: 700 }}>{items.length}</span> / {totalCount} Loaded
        </div>
      </div>
      )}

      {/* Warehouse Items Table with Vertical Scroll Bar & Automatic Infinite Load */}
      <div
        onScroll={handleScroll}
        style={{
          maxHeight: '400px',
          overflowY: 'auto',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          background: 'var(--bg-card)'
        }}
      >
        <table id="warehouse-analytics-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
          <thead style={{ position: 'sticky', top: 0, background: '#161B22', zIndex: 2 }}>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '12px 10px' }}>Warehouse</th>
              <th style={{ padding: '12px 10px' }}>Order Date</th>
              <th style={{ padding: '12px 10px' }}>Batch ID</th>
              <th style={{ padding: '12px 10px' }}>Invoice #</th>
              <th style={{ padding: '12px 10px' }}>Customer Item Code</th>
              <th style={{ padding: '12px 10px' }}>C&S Item Code</th>
              <th style={{ padding: '12px 10px' }}>Cases Built Qty</th>
              <th style={{ padding: '12px 10px' }}>Order Qty</th>
              <th style={{ padding: '12px 10px' }}>Scratch Qty</th>
              <th style={{ padding: '12px 10px' }}>Sub Item (sl_itm_ind)</th>
              <th style={{ padding: '12px 10px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: '24px', color: 'var(--color-primary-light)', fontWeight: 600 }}>
                  Querying PostgreSQL Warehouse Statistics...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-secondary)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '14px' }}>
                    No Database Records Found for Selected Date ({globalDate || 'No Date'})
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    PostgreSQL {globalTargetDb.toUpperCase()} has 0 records matching the selected date & filter parameters. Please change the date picker above.
                  </div>
                </td>
              </tr>
            ) : (
              items.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '10px', fontWeight: 700, color: 'var(--color-cyan)' }}>{item.whs_num}</td>
                  <td style={{ padding: '10px', color: '#60a5fa', fontWeight: 600, fontFamily: 'monospace' }}>{item.oerdte || '—'}</td>
                  <td style={{ padding: '10px', color: '#f59e0b', fontWeight: 600, fontFamily: 'monospace' }}>{item.batch_id || '—'}</td>
                  <td style={{ padding: '10px', color: 'var(--color-primary)' }}>{item.invc_num_stg}</td>
                  <td style={{ padding: '10px' }}>{item.cust_item_code}</td>
                  <td style={{ padding: '10px', color: '#34d399', fontWeight: 600 }}>{item.cs_item_code}</td>
                  <td style={{ padding: '10px', fontWeight: 700 }}>{item.cases_bld_stg}</td>
                  <td style={{ padding: '10px' }}>{item.orgnl_ordr_qty_stg}</td>
                  <td style={{ padding: '10px', color: '#ef4444' }}>{item.whs_scrtch_qty_stg}</td>
                  <td style={{ padding: '10px' }}>
                    <span className="badge" style={{ background: 'rgba(124,58,237,0.2)', color: '#c084fc' }}>
                      {item.sl_itm_ind_stg}
                    </span>
                  </td>
                  <td style={{ padding: '10px' }}>
                    <span className={`badge ${item.procurement_transfer_status === 'COMPLETED' ? 'badge-green' : 'badge-amber'}`}>
                      ● {item.procurement_transfer_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {loadingMore && (
          <div style={{ textAlign: 'center', padding: '12px', fontSize: '12px', color: 'var(--color-primary-light)', fontWeight: 600 }}>
            Loading next records...
          </div>
        )}
      </div>

      {/* Pagination Controls Bar */}
      {!noDataForDate && items.length > 0 && (
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)',
          flexWrap: 'wrap', gap: '10px'
        }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Showing <strong style={{ color: 'var(--text-primary)' }}>{items.length}</strong> of <strong style={{ color: 'var(--color-primary-light)' }}>{totalCount}</strong> total items
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => {
                if (items.length > 20) setItems(items.slice(0, Math.max(20, items.length - 20)));
              }}
              disabled={items.length <= 20}
              style={{
                background: items.length <= 20 ? 'rgba(255,255,255,0.05)' : 'var(--bg-secondary)',
                color: items.length <= 20 ? 'var(--text-muted)' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '4px 12px', borderRadius: '6px', fontSize: '12px',
                cursor: items.length <= 20 ? 'not-allowed' : 'pointer',
                fontWeight: 600
              }}
            >
              ← Previous 20
            </button>

            <span style={{ fontSize: '12px', fontWeight: 700, color: '#a78bfa', background: 'rgba(124,58,237,0.15)', padding: '4px 10px', borderRadius: '6px' }}>
              Page 1 of {Math.max(1, Math.ceil(totalCount / 20))}
            </span>

            <button
              onClick={loadMoreData}
              disabled={!hasMore || loadingMore}
              style={{
                background: !hasMore ? 'rgba(255,255,255,0.05)' : 'var(--color-primary)',
                color: '#ffffff',
                border: 'none',
                padding: '4px 12px', borderRadius: '6px', fontSize: '12px',
                cursor: !hasMore ? 'not-allowed' : 'pointer',
                fontWeight: 600
              }}
            >
              {loadingMore ? 'Loading...' : 'Next 20 →'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

new_admin_css = """/* =============================================================
   13. RESTAURANT OPERATIONS COMMAND CENTER & KDS (MODERN MINIMALIST LIGHT)
   ============================================================= */

/* Clean Modern Minimalist Operations Canvas */
body.admin-portal-body {
    background-color: var(--bg-page);
    color: var(--text-body);
    font-family: var(--font-family);
    min-height: 100vh;
}

/* Operations Topbar - Clean White Sticky Glassmorphism */
.admin-topbar {
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    padding: 14px 28px;
    box-shadow: var(--shadow-subtle);
}

.admin-topbar-container {
    max-width: 1440px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.admin-brand-cluster {
    display: flex;
    align-items: center;
    gap: 14px;
}

.admin-brand-link {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--text-main);
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.03em;
}

.admin-brand-title strong {
    color: var(--primary);
}

.admin-badge-ops {
    background: var(--primary-subtle);
    color: var(--primary);
    border: 1px solid var(--primary-border);
    padding: 4px 10px;
    border-radius: var(--radius-full);
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Live Kitchen Pulse Indicator */
.admin-live-pulse {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--veg-color);
    background: var(--veg-bg);
    border: 1px solid #BBF7D0;
    padding: 4px 12px;
    border-radius: var(--radius-full);
}

.pulse-green-dot {
    width: 8px;
    height: 8px;
    background: #16A34A;
    border-radius: 50%;
    box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7);
    animation: pulseGreenBeacon 2s infinite;
}

@keyframes pulseGreenBeacon {
    0% {
        box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7);
    }
    70% {
        box-shadow: 0 0 0 8px rgba(22, 163, 74, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(22, 163, 74, 0);
    }
}

.admin-actions-cluster {
    display: flex;
    align-items: center;
    gap: 16px;
}

/* Direct switcher to switch back to customer store */
.btn-view-store {
    background: var(--surface);
    color: var(--text-main);
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 8px 16px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    transition: var(--transition);
}

.btn-view-store:hover {
    background: var(--surface-hover);
    border-color: var(--border-dark);
}

/* Access Denied Guard Box (403) */
.admin-access-denied {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80vh;
    padding: 24px;
}

.admin-access-denied.hidden {
    display: none !important;
}

.denied-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 48px 36px;
    max-width: 520px;
    text-align: center;
    box-shadow: var(--shadow-card-hover);
}

.denied-card h2 {
    font-size: 1.45rem;
    font-weight: 800;
    color: #DC2626;
    margin-bottom: 12px;
}

.denied-card p {
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 24px;
}

.btn-denied-login {
    background: var(--primary);
    color: #FFFFFF;
    border: none;
    padding: 12px 24px;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
}

.btn-denied-login:hover {
    background: var(--primary-hover);
}

/* Main Operations Container */
.admin-main-container {
    max-width: 1440px;
    margin: 0 auto;
    padding: 32px 28px 64px;
}

.admin-main-container.hidden {
    display: none !important;
}

/* 4 Executive KPI Metric Cards */
.admin-metrics-ribbon {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    margin-bottom: 28px;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 22px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: var(--shadow-card);
    transition: var(--transition);
}

.metric-card:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.metric-icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 800;
    flex-shrink: 0;
}

.metric-icon-wrap.bg-green {
    background: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
}

.metric-icon-wrap.bg-blue {
    background: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
}

.metric-icon-wrap.bg-orange {
    background: #FFFBEB;
    color: #D97706;
    border: 1px solid #FDE68A;
}

.metric-icon-wrap.bg-purple {
    background: #F5F3FF;
    color: #7C3AED;
    border: 1px solid #DDD6FE;
}

.metric-details {
    display: flex;
    flex-direction: column;
}

.metric-label {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.metric-details h3 {
    font-size: 1.85rem;
    font-weight: 800;
    color: var(--text-main);
    margin: 0;
    line-height: 1.1;
    letter-spacing: -0.02em;
}

.metric-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 4px;
    font-weight: 500;
}

/* Console Navigation Bar */
.admin-controls-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 12px 18px;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 14px;
    box-shadow: var(--shadow-card);
}

.admin-mode-tabs {
    display: flex;
    gap: 8px;
    background: var(--surface-sunken);
    padding: 4px;
    border-radius: var(--radius-md);
}

.admin-mode-btn {
    background: transparent;
    color: var(--text-muted);
    border: none;
    padding: 10px 20px;
    border-radius: var(--radius-sm);
    font-size: 0.9rem;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 8px;
}

.admin-mode-btn:hover {
    color: var(--text-main);
}

.admin-mode-btn.active {
    background: var(--surface);
    color: var(--text-main);
    box-shadow: var(--shadow-subtle);
}

.btn-util-refresh {
    background: var(--surface);
    color: var(--text-main);
    border: 1.5px solid var(--border);
    padding: 10px 18px;
    border-radius: var(--radius-md);
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: var(--transition);
}

.btn-util-refresh:hover {
    background: var(--surface-hover);
    border-color: var(--border-dark);
}

/* KDS Filter Toolbar */
.kds-filter-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 14px;
}

.kds-status-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.order-filter-btn {
    background: var(--surface);
    color: var(--text-muted);
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: var(--radius-full);
    font-size: 0.84rem;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
}

.order-filter-btn:hover {
    background: var(--surface-hover);
    color: var(--text-main);
}

.order-filter-btn.active {
    background: var(--text-main);
    color: #FFFFFF;
    border-color: var(--text-main);
}

.kds-search-box {
    position: relative;
    width: 320px;
}

.kds-search-box input {
    width: 100%;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 16px;
    color: var(--text-main);
    font-size: 0.9rem;
    font-family: inherit;
    outline: none;
    transition: var(--transition);
}

.kds-search-box input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.12);
}

.kds-search-box input::placeholder {
    color: var(--text-faint);
}

/* KDS Tickets Grid - Multi-Column Responsive Masonry */
.kds-tickets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 24px;
    align-items: start;
}

.kds-tickets-grid.empty-state-active {
    display: block;
}

/* KDS Order Ticket Card */
.kds-ticket-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 380px;
    box-shadow: var(--shadow-card);
    transition: var(--transition);
    position: relative;
}

.kds-ticket-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-card-hover);
}

/* Color-coded Status Top Stripe */
.kds-ticket-card.kds-status-pending {
    border-top: 5px solid #F59E0B;
}

.kds-ticket-card.kds-status-preparing {
    border-top: 5px solid #3B82F6;
}

.kds-ticket-card.kds-status-delivering {
    border-top: 5px solid #8B5CF6;
}

.kds-ticket-card.kds-status-delivered {
    border-top: 5px solid #10B981;
}

.kds-ticket-card.kds-status-cancelled {
    border-top: 5px solid #EF4444;
    opacity: 0.65;
}

/* Ticket Header */
.ticket-header {
    padding: 16px 20px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-light);
    background: #FFFFFF;
}

.ticket-id-wrap {
    display: flex;
    align-items: baseline;
    gap: 8px;
}

.ticket-id {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.02em;
}

.ticket-time-ago {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
}

/* Ticket Badges */
.ticket-badge {
    font-size: 0.75rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.badge-pending {
    background: #FEF3C7;
    color: #92400E;
}

.badge-preparing {
    background: #DBEAFE;
    color: #1E40AF;
}

.badge-delivering {
    background: #EDE9FE;
    color: #5B21B6;
}

.badge-delivered {
    background: #DCFCE7;
    color: #166534;
}

.badge-cancelled {
    background: #FEE2E2;
    color: #991B1B;
}

/* Customer Details Block */
.ticket-customer-info {
    padding: 14px 20px;
    background: var(--surface-sunken);
    border-bottom: 1px solid var(--border-light);
}

.customer-name {
    font-size: 0.95rem;
    font-weight: 800;
    color: var(--text-main);
    margin-bottom: 4px;
}

.customer-meta {
    font-size: 0.82rem;
    color: var(--text-muted);
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-weight: 500;
}

/* Food Items List Inside Ticket */
.ticket-items-list {
    padding: 16px 20px;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 220px;
    overflow-y: auto;
}

.ticket-item-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.9rem;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border-light);
}

.ticket-item-row:last-child {
    border-bottom: none;
}

.ticket-item-qty {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    background: var(--primary-subtle);
    color: var(--primary);
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.8rem;
    margin-right: 8px;
    padding: 0 4px;
}

.ticket-item-name {
    color: var(--text-main);
    font-weight: 600;
    flex-grow: 1;
}

/* Ticket Total & Payment Summary */
.ticket-footer-summary {
    padding: 14px 20px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
}

.ticket-pay-badge {
    font-size: 0.75rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.ticket-pay-pending {
    background: #FEF3C7;
    color: #92400E;
}

.ticket-pay-paid {
    background: #DCFCE7;
    color: #166534;
}

.ticket-total-price {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.02em;
}

/* Action Progression Buttons */
.ticket-actions-bar {
    padding: 14px 20px 18px;
    display: flex;
    gap: 10px;
    background: #FFFFFF;
    border-top: 1px solid var(--border-light);
}

.btn-kds-action {
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: var(--radius-md);
    font-family: inherit;
    font-size: 0.92rem;
    font-weight: 800;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn-kds-cook {
    background: #2563EB;
    color: #FFFFFF;
}

.btn-kds-cook:hover {
    background: #1D4ED8;
}

.btn-kds-dispatch {
    background: #7C3AED;
    color: #FFFFFF;
}

.btn-kds-dispatch:hover {
    background: #6D28D9;
}

.btn-kds-deliver {
    background: #059669;
    color: #FFFFFF;
}

.btn-kds-deliver:hover {
    background: #047857;
}

.btn-kds-cancel {
    background: transparent;
    color: var(--text-muted);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-md);
    padding: 10px 14px;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: var(--transition);
}

.btn-kds-cancel:hover {
    background: #FEE2E2;
    color: #DC2626;
    border-color: #FCA5A5;
}

.btn-kds-action:disabled,
.btn-kds-cancel:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* =============================================================
   INVENTORY & 80-DISH STOCK CENTER (VIEW 2)
   ============================================================= */

.inventory-card-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px;
    box-shadow: var(--shadow-card);
}

.inventory-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-light);
}

.inventory-header-info h2 {
    font-size: 1.45rem;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.02em;
    margin-bottom: 4px;
}

.inventory-header-info p {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.inventory-search-wrap {
    position: relative;
    width: 320px;
}

.inventory-search-wrap input {
    width: 100%;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 16px;
    color: var(--text-main);
    font-size: 0.9rem;
    font-family: inherit;
    outline: none;
    transition: var(--transition);
}

.inventory-search-wrap input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.12);
}

/* Category Filter Tabs inside Inventory */
.inventory-category-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    overflow-x: auto;
    padding-bottom: 6px;
}

.inv-cat-btn {
    background: var(--surface);
    color: var(--text-muted);
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: var(--radius-full);
    font-size: 0.84rem;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
    transition: var(--transition);
}

.inv-cat-btn:hover {
    color: var(--text-main);
    background: var(--surface-hover);
}

.inv-cat-btn.active {
    background: var(--primary);
    color: #FFFFFF;
    border-color: var(--primary);
}

/* Clean Operations Table */
.inventory-table-wrap {
    overflow-x: auto;
}

.inventory-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.92rem;
}

.inventory-table th {
    background: var(--surface-sunken);
    color: var(--text-muted);
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
}

.inventory-table td {
    padding: 16px 18px;
    border-bottom: 1px solid var(--border-light);
    color: var(--text-main);
    vertical-align: middle;
}

.inventory-table tr:hover {
    background: var(--surface-hover);
}

.inv-dish-meta {
    display: flex;
    align-items: center;
    gap: 14px;
}

.inv-dish-thumb {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-sm);
    object-fit: cover;
    background: var(--surface-sunken);
    border: 1px solid var(--border);
}

.inv-dish-title {
    font-weight: 800;
    color: var(--text-main);
    margin-bottom: 2px;
}

.inv-dish-desc {
    font-size: 0.8rem;
    color: var(--text-muted);
    max-width: 320px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* iOS-Style Instant Stock Toggle Switch */
.stock-switch-wrap {
    display: inline-flex;
    align-items: center;
    gap: 10px;
}

.stock-toggle-switch {
    position: relative;
    display: inline-block;
    width: 46px;
    height: 24px;
}

.stock-toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.stock-toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--border-dark);
    transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 9999px;
}

.stock-toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.stock-toggle-switch input:checked + .stock-toggle-slider {
    background-color: var(--veg-color);
}

.stock-toggle-switch input:checked + .stock-toggle-slider:before {
    transform: translateX(22px);
}

.stock-status-label {
    font-size: 0.82rem;
    font-weight: 700;
    min-width: 80px;
}

.stock-status-label.in-stock {
    color: var(--veg-color);
}

.stock-status-label.out-of-stock {
    color: var(--nonveg-color);
}

/* Responsive Breakpoints for Tablet & Mobile */
@media (max-width: 900px) {
    .admin-topbar-container {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
    }

    .admin-controls-bar,
    .kds-filter-toolbar,
    .inventory-panel-header {
        flex-direction: column;
        align-items: stretch;
    }

    .kds-search-box,
    .inventory-search-wrap {
        width: 100%;
    }

    .kds-tickets-grid {
        grid-template-columns: 1fr;
    }

    .controls-container {
        flex-direction: column;
        align-items: stretch;
    }

    .search-box {
        flex: 1 1 100%;
    }

    .hero-content h1 {
        font-size: 2.2rem;
    }

    .checkout-grid {
        grid-template-columns: 1fr;
    }

    .tracking-details-grid {
        grid-template-columns: 1fr;
    }

    .form-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 640px) {
    .stepper-track {
        flex-direction: column;
        gap: 18px;
        align-items: flex-start;
    }

    .step-item {
        flex-direction: row;
        gap: 14px;
        text-align: left;
    }

    .step-line {
        display: none;
    }

    .nav-container {
        padding: 12px 16px;
    }

    .checkout-main,
    .tracking-main,
    .admin-main-container {
        padding: 0 16px;
    }
}
"""

with open('scratch/new_admin.css', 'w', encoding='utf-8') as f:
    f.write(new_admin_css)

print('Lines:', len(new_admin_css.splitlines()))
print('Chars:', len(new_admin_css))

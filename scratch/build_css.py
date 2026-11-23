with open('frontend/css/style.css', 'r', encoding='utf-8') as f:
    full = f.read()

idx_badges = full.find('/* -------------------------------------------------------------\n   9. CUSTOMER STATUS BADGES & BANNER')
part_a = full[:idx_badges]

with open('scratch/old_admin.css', 'r', encoding='utf-8') as f:
    part_admin = f.read()

middle = """/* -------------------------------------------------------------
   9. CHECKOUT PAGE STYLING (MODERN MINIMALIST LIGHT)
   ------------------------------------------------------------- */
.back-link {
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 700;
    font-size: 0.9rem;
    transition: var(--transition);
}

.back-link:hover {
    color: var(--primary);
}

.checkout-main {
    max-width: 1140px;
    margin: 36px auto 64px;
    padding: 0 24px;
}

.checkout-header {
    margin-bottom: 28px;
}

.checkout-header h1 {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: var(--text-main);
    margin-bottom: 6px;
}

.checkout-header p {
    color: var(--text-muted);
    font-size: 0.95rem;
}

.checkout-grid {
    display: grid;
    grid-template-columns: 1.45fr 1fr;
    gap: 32px;
    align-items: start;
}

.checkout-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px;
    box-shadow: var(--shadow-card);
}

.checkout-card h3 {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-main);
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border-light);
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 6px;
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 12px 16px;
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: inherit;
    font-size: 0.95rem;
    color: var(--text-main);
    background: #FFFFFF;
    transition: var(--transition);
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.12);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
    color: var(--text-faint);
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.error-msg {
    color: var(--nonveg-color);
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 5px;
    display: block;
}

/* Modern Selectable Payment Option Cards */
.payment-options {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.payment-option {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    border: 1.5px solid var(--border);
    border-radius: var(--radius-md);
    background: #FFFFFF;
    cursor: pointer;
    transition: var(--transition);
}

.payment-option:hover {
    background: var(--surface-hover);
    border-color: var(--border-dark);
}

.payment-option.selected {
    border-color: var(--primary);
    background: var(--primary-subtle);
    box-shadow: 0 0 0 1px var(--primary);
}

.payment-option input[type="radio"] {
    accent-color: var(--primary);
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.payment-text {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-main);
}

/* Order Summary Items Breakdown */
.checkout-items-list {
    max-height: 320px;
    overflow-y: auto;
    margin-bottom: 20px;
    padding-right: 4px;
}

.checkout-item-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-light);
}

.checkout-item-row:last-child {
    border-bottom: none;
}

.checkout-item-info h4 {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 2px;
}

.checkout-item-info span {
    font-size: 0.84rem;
    color: var(--text-muted);
}

.checkout-item-price {
    font-weight: 800;
    font-size: 0.96rem;
    color: var(--text-main);
}

.checkout-pricing {
    border-top: 1px solid var(--border);
    padding-top: 16px;
    margin-bottom: 20px;
}

.guarantee-box {
    background: var(--surface-sunken);
    border: 1px dashed var(--border-dark);
    padding: 14px 16px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-muted);
    font-size: 0.84rem;
    font-weight: 500;
}

.checkout-submit-btn {
    border: none;
    cursor: pointer;
    margin-top: 18px;
}

/* -------------------------------------------------------------
   10. ORDER TRACKING & STEPPER STYLING (MODERN MINIMALIST LIGHT)
   ------------------------------------------------------------- */
.tracking-main {
    max-width: 1040px;
    margin: 36px auto 64px;
    padding: 0 24px;
}

.tracking-header {
    text-align: center;
    margin-bottom: 32px;
}

.success-badge {
    display: inline-block;
    background: #ECFDF5;
    color: var(--veg-color);
    font-weight: 800;
    font-size: 0.82rem;
    padding: 5px 14px;
    border-radius: var(--radius-full);
    border: 1px solid #BBF7D0;
    margin-bottom: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.tracking-header h1 {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: var(--text-main);
    margin-bottom: 6px;
}

.tracking-header p {
    color: var(--text-muted);
    font-size: 1rem;
}

.tracking-header p strong {
    color: var(--text-main);
    font-weight: 700;
}

/* 4-Stage Modern Stepper */
.stepper-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 36px 28px;
    margin-bottom: 32px;
    box-shadow: var(--shadow-card);
}

.stepper-track {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 820px;
    margin: 0 auto;
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
    opacity: 0.38;
    transition: var(--transition);
}

.step-item.active {
    opacity: 1;
}

.step-circle {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #F4F4F5;
    border: 2px solid #E4E4E7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text-muted);
    transition: var(--transition);
}

.step-item.active .step-circle {
    background: var(--primary);
    border-color: var(--primary);
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(225, 29, 72, 0.35);
    transform: scale(1.08);
}

.step-label strong {
    display: block;
    font-size: 0.94rem;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.01em;
}

.step-label small {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
}

.step-line {
    flex-grow: 1;
    height: 3px;
    background: #E4E4E7;
    margin: 0 12px;
    position: relative;
    top: -16px;
    transition: var(--transition);
}

.step-line.active {
    background: var(--primary);
}

/* Tracking Details & Receipt Grid */
.tracking-details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
}

.tracking-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 26px;
    box-shadow: var(--shadow-card);
}

.tracking-card h3 {
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-main);
    margin-bottom: 18px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-light);
}

.details-list {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.detail-row {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.detail-label {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.detail-row strong,
.detail-row span,
.detail-row p {
    font-size: 0.94rem;
    color: var(--text-main);
    font-weight: 600;
}

.detail-row p {
    font-weight: 500;
    line-height: 1.45;
}

.receipt-items-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
}

.receipt-item-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-light);
}

.receipt-item-row strong {
    font-size: 0.92rem;
    color: var(--text-main);
    font-weight: 700;
}

.receipt-item-row small {
    display: block;
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 1px;
}

.receipt-item-row span {
    font-weight: 800;
    font-size: 0.94rem;
    color: var(--text-main);
}

.receipt-total-box {
    border-top: 1px solid var(--border);
    padding-top: 14px;
}

/* -------------------------------------------------------------
   11. REAL-TIME TELEMETRY & LEAFLET MAP STYLING
   ------------------------------------------------------------- */
.map-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    margin-bottom: 28px;
    overflow: hidden;
    box-shadow: var(--shadow-card);
}

.map-header {
    padding: 18px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    border-bottom: 1px solid var(--border);
}

.map-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-main);
}

.map-status-desc {
    font-size: 0.84rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* Pulsing Real-Time WebSocket Telemetry Pill */
.live-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: var(--radius-full);
    font-size: 0.82rem;
    font-weight: 800;
    background: #EEF2FF;
    color: #4338CA;
    border: 1px solid #C7D2FE;
}

.live-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #16A34A;
    box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7);
    animation: pulse-green 1.8s infinite;
}

@keyframes pulse-green {
    0% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7);
    }
    70% {
        transform: scale(1);
        box-shadow: 0 0 0 8px rgba(22, 163, 74, 0);
    }
    100% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(22, 163, 74, 0);
    }
}

/* Leaflet Canvas Container */
#tracking-map {
    height: 380px;
    width: 100%;
    z-index: 10;
}

.map-footer {
    padding: 12px 24px;
    background: var(--surface-sunken);
    border-top: 1px solid var(--border);
    font-size: 0.84rem;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.map-footer strong {
    color: var(--text-main);
}

/* Clean Custom Map Marker Badges */
.custom-map-icon {
    display: flex;
    align-items: center;
    justify-content: center;
}

.map-pin-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 0.88rem;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.25);
    border: 2px solid #FFFFFF;
}

.kitchen-pin {
    background: #E11D48;
}

.customer-pin {
    background: #2563EB;
}

.rider-pin {
    background: #16A34A;
}

.icon-kitchen {
    width: 36px;
    height: 36px;
}

.icon-customer {
    width: 36px;
    height: 36px;
}

.icon-rider {
    width: 42px;
    height: 42px;
    transition: all 0.5s ease-in-out;
}

/* -------------------------------------------------------------
   12. CUSTOMER STATUS BADGES & ORDER HISTORY
   ------------------------------------------------------------- */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.status-pending {
    background-color: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
}

.status-preparing {
    background-color: #DBEAFE;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
}

.status-out_for_delivery {
    background-color: #E0E7FF;
    color: #3730A3;
    border: 1px solid #C7D2FE;
}

.status-delivered {
    background-color: #DCFCE7;
    color: #166534;
    border: 1px solid #BBF7D0;
}

.status-cancelled {
    background-color: #FEE2E2 !important;
    color: #991B1B !important;
    border: 1px solid #FCA5A5 !important;
}

.order-cancelled-banner {
    background: #FEF2F2;
    border: 1px solid #FCA5A5;
    color: #991B1B;
    padding: 16px 20px;
    border-radius: var(--radius-md);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 0.95rem;
}
"""

responsive = """/* -------------------------------------------------------------
   14. RESPONSIVE BREAKPOINTS (TABLET & MOBILE)
   ------------------------------------------------------------- */
@media (max-width: 900px) {
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
    .tracking-main {
        padding: 0 16px;
    }
}
"""

combined = (
    part_a.rstrip() + 
    "\n\n" + 
    middle.strip() + 
    "\n\n/* =============================================================\n   13. " + 
    part_admin.strip() + 
    "\n\n" + 
    responsive.strip() + 
    "\n"
)

with open('scratch/full_style.css', 'w', encoding='utf-8') as f:
    f.write(combined)

print('Assembled scratch/full_style.css successfully!')
print('Lines:', len(combined.splitlines()))
print('Characters:', len(combined))

with open('scratch/build_css.py', 'r', encoding='utf-8') as f:
    text = f.read()

p_mid = text.find('middle = """') + len('middle = """')
p_mid_end = text.find('"""\n\nresponsive =')
middle = text[p_mid:p_mid_end]

with open('frontend/css/style.css', 'r', encoding='utf-8') as f:
    curr = f.read()

idx_badges = curr.find('/* -------------------------------------------------------------\n   9. CUSTOMER STATUS BADGES & BANNER')
part_a = curr[:idx_badges]

idx_admin = curr.find('/* =============================================================\n   10. ADMIN CONSOLE')
idx_admin_end = curr.find('/* Responsive adjustments */')
admin = curr[idx_admin:idx_admin_end].replace('10. ADMIN CONSOLE', '13. ADMIN CONSOLE')

resp = """/* -------------------------------------------------------------
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

full_css = part_a.rstrip() + '\n\n' + middle.strip() + '\n\n' + admin.strip() + '\n\n' + resp.strip() + '\n'
print('Lines:', len(full_css.splitlines()))
print('Chars:', len(full_css))
print('Estimated tokens (~3.8 chars/tok):', int(len(full_css)/3.8))

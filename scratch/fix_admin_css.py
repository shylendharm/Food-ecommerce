with open('scratch/new_admin.css', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace admin-main-container.hidden with general .hidden
text = text.replace(
""".admin-main-container.hidden {
    display: none !important;
}""",
""".hidden,
.admin-view-section.hidden,
.admin-main-container.hidden {
    display: none !important;
}"""
)

# Replace btn-kds-cancel
old_cancel = """.btn-kds-cancel {
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
}"""

new_cancel = """.btn-kds-cancel {
    background: transparent;
    color: #DC2626;
    border: 1.5px solid #FCA5A5;
    border-radius: var(--radius-md);
    padding: 10px 16px;
    font-family: inherit;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: var(--transition);
    white-space: nowrap;
}

.btn-kds-cancel:hover {
    background: #FEE2E2;
    color: #991B1B;
    border-color: #EF4444;
}"""

text = text.replace(old_cancel, new_cancel)

with open('scratch/new_admin_fixed.css', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated scratch/new_admin_fixed.css successfully!')
print('Lines:', len(text.splitlines()))
print('Chars:', len(text))

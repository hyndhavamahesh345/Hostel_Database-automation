/**
 * HOSTEL ACCOMMODATION AND STUDENT SERVICES MANAGEMENT SYSTEM
 * Core Client-Side Logic & UI Interactivity
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target) && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        });
    }

    // 2. Auto Dismiss Flash Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => alert.remove());
        }
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // 3. Modal Management (Data attribute based: data-open-modal="modal-id")
    const modalTriggers = document.querySelectorAll('[data-open-modal]');
    const modalCloses = document.querySelectorAll('[data-close-modal]');
    
    modalTriggers.forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-open-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    modalCloses.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });

    // Close modal on background click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });

    // 4. Quick Demo Login Fillers
    window.fillDemoLogin = function(username, password) {
        const userInput = document.getElementById('login-username');
        const passInput = document.getElementById('login-password');
        if (userInput && passInput) {
            userInput.value = username;
            passInput.value = password;
            userInput.style.backgroundColor = '#eef2ff';
            passInput.style.backgroundColor = '#eef2ff';
            setTimeout(() => {
                userInput.style.backgroundColor = '';
                passInput.style.backgroundColor = '';
            }, 500);
        }
    };

    // 5. Client-Side Quick Table Search Filtering
    const searchInputs = document.querySelectorAll('[data-table-filter]');
    searchInputs.forEach(input => {
        input.addEventListener('input', () => {
            const targetTableId = input.getAttribute('data-table-filter');
            const table = document.getElementById(targetTableId);
            if (!table) return;
            
            const term = input.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    });

    // 6. Form Submission Confirmation Dialogs
    const confirmForms = document.querySelectorAll('[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const msg = form.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // 7. Event Delegation for Data-Action Buttons
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;

        const action = btn.getAttribute('data-action');
        
        if (action === 'fill-demo') {
            const u = btn.getAttribute('data-username');
            const p = btn.getAttribute('data-password');
            if (u && p) window.fillDemoLogin(u, p);
        }
        else if (action === 'edit-student') {
            openEditStudentModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-name'),
                btn.getAttribute('data-email'),
                btn.getAttribute('data-phone'),
                btn.getAttribute('data-course'),
                btn.getAttribute('data-year'),
                btn.getAttribute('data-gender'),
                btn.getAttribute('data-emergency'),
                btn.getAttribute('data-guardian'),
                btn.getAttribute('data-address')
            );
        }
        else if (action === 'edit-room') {
            openEditRoomModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-type'),
                btn.getAttribute('data-capacity'),
                btn.getAttribute('data-fee'),
                btn.getAttribute('data-status')
            );
        }
        else if (action === 'update-complaint') {
            openUpdateComplaintModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-title'),
                btn.getAttribute('data-status'),
                btn.getAttribute('data-notes')
            );
        }
        else if (action === 'record-payment') {
            openRecordPaymentModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-student'),
                btn.getAttribute('data-due')
            );
        }
        else if (action === 'transfer-student') {
            openTransferModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-student'),
                btn.getAttribute('data-room')
            );
        }
        else if (action === 'pay-fee') {
            openStudentPayModal(
                btn.getAttribute('data-id'),
                btn.getAttribute('data-term'),
                btn.getAttribute('data-due')
            );
        }
    });
});

/**
 * Helper to populate Edit Student modal with selected row data
 */
function openEditStudentModal(id, name, email, phone, course, year, gender, emergency, guardian, address) {
    const el = (i) => document.getElementById(i);
    if (el('edit_student_id')) el('edit_student_id').value = id || '';
    if (el('edit_name')) el('edit_name').value = name || '';
    if (el('edit_email')) el('edit_email').value = email || '';
    if (el('edit_phone')) el('edit_phone').value = phone || '';
    if (el('edit_course')) el('edit_course').value = course || '';
    if (el('edit_year')) el('edit_year').value = year || '';
    if (el('edit_gender')) el('edit_gender').value = gender || 'Female';
    if (el('edit_emergency_contact')) el('edit_emergency_contact').value = emergency || '';
    if (el('edit_guardian_name')) el('edit_guardian_name').value = guardian || '';
    if (el('edit_address')) el('edit_address').value = address || '';
    
    const modal = document.getElementById('editStudentModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Helper to populate Edit Room modal
 */
function openEditRoomModal(id, roomType, capacity, fee, status) {
    const el = (i) => document.getElementById(i);
    if (el('edit_room_id')) el('edit_room_id').value = id || '';
    if (el('edit_room_type')) el('edit_room_type').value = roomType || '';
    if (el('edit_capacity')) el('edit_capacity').value = capacity || '';
    if (el('edit_fee_per_semester')) el('edit_fee_per_semester').value = fee || '';
    if (el('edit_status')) el('edit_status').value = status || 'Available';
    
    const modal = document.getElementById('editRoomModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Helper to populate Update Complaint modal
 */
function openUpdateComplaintModal(id, title, status, notes) {
    const el = (i) => document.getElementById(i);
    if (el('complaint_id_input')) el('complaint_id_input').value = id || '';
    if (el('complaint_title_display')) el('complaint_title_display').textContent = `#${id || ''}: ${title || ''}`;
    if (el('complaint_status_select')) el('complaint_status_select').value = status || 'Pending';
    if (el('complaint_notes_input')) el('complaint_notes_input').value = notes || '';
    
    const modal = document.getElementById('updateComplaintModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Helper to populate Record Payment modal
 */
function openRecordPaymentModal(feeId, studentName, dueAmount) {
    const el = (i) => document.getElementById(i);
    if (el('payment_fee_id')) el('payment_fee_id').value = feeId || '';
    if (el('payment_student_display')) el('payment_student_display').textContent = studentName || '';
    if (el('payment_due_display')) el('payment_due_display').textContent = `₹${parseFloat(dueAmount || 0).toLocaleString('en-IN')}`;
    if (el('payment_amount_input')) {
        el('payment_amount_input').value = dueAmount || 0;
        el('payment_amount_input').max = dueAmount || 0;
    }
    
    const modal = document.getElementById('recordPaymentModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Helper to populate Transfer Student modal
 */
function openTransferModal(allocationId, studentName, currentRoom) {
    const el = (i) => document.getElementById(i);
    if (el('transfer_allocation_id')) el('transfer_allocation_id').value = allocationId || '';
    if (el('transfer_student_display')) el('transfer_student_display').textContent = `${studentName || ''} (Current Room: ${currentRoom || 'None'})`;
    
    const modal = document.getElementById('transferModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Helper to populate Student Fee Payment Modal
 */
function openStudentPayModal(feeId, term, dueAmount) {
    const el = (i) => document.getElementById(i);
    if (el('pay_fee_id')) el('pay_fee_id').value = feeId || '';
    if (el('pay_term_display')) el('pay_term_display').textContent = term || '';
    if (el('pay_due_display')) el('pay_due_display').textContent = `₹${parseFloat(dueAmount || 0).toLocaleString('en-IN')}`;
    if (el('pay_amount_input')) {
        el('pay_amount_input').value = dueAmount || 0;
        el('pay_amount_input').max = dueAmount || 0;
    }
    
    const modal = document.getElementById('payFeeModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

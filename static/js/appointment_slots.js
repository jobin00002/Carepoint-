/**
 * CarePoint 15-Minute Slot Selector (Requirement 3 & 4)
 * - Fetches 15-minute slots for selected doctor & date
 * - Disables and marks already booked slots (Prevents double booking)
 * - Highlights selected slot and updates appointment form
 */

document.addEventListener('DOMContentLoaded', () => {
    const doctorSelect = document.getElementById('doctor_select');
    const dateInput = document.getElementById('appointment_date_input');
    const slotsContainer = document.getElementById('slots_container');
    const selectedSlotInput = document.getElementById('selected_time_slot');
    const selectedSlotSummary = document.getElementById('selected_slot_summary');
    const emergencyCheckbox = document.getElementById('is_emergency_checkbox');
    const emergencyWarning = document.getElementById('emergency_swap_alert');

    if (!doctorSelect || !dateInput || !slotsContainer) return;

    function fetchSlots() {
        const doctorId = doctorSelect.value;
        const dateVal = dateInput.value;

        if (!doctorId || !dateVal) {
            slotsContainer.innerHTML = `
                <div class="col-12 text-center py-4 text-muted">
                    <i class="fa-solid fa-calendar-check fa-2x mb-2 text-primary opacity-50"></i>
                    <p class="mb-0">Please select a doctor and date to view available 15-minute time slots.</p>
                </div>`;
            return;
        }

        slotsContainer.innerHTML = `
            <div class="col-12 text-center py-4">
                <div class="spinner-border text-primary spinner-border-sm" role="status"></div>
                <span class="ms-2 text-muted">Loading 15-minute consultation slots...</span>
            </div>`;

        fetch(`/api/slots/?doctor_id=${doctorId}&date=${dateVal}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    slotsContainer.innerHTML = `<div class="col-12 text-danger p-3">${data.error}</div>`;
                    return;
                }

                if (!data.slots || data.slots.length === 0) {
                    slotsContainer.innerHTML = `
                        <div class="col-12 text-center py-4 text-muted">
                            <i class="fa-solid fa-ban fa-2x mb-2 text-secondary"></i>
                            <p class="mb-0">No appointment slots available for this doctor on selected date.</p>
                        </div>`;
                    return;
                }

                let html = '<div class="slot-grid">';
                data.slots.forEach(slot => {
                    const isBooked = slot.is_booked;
                    const pillClass = isBooked ? 'slot-pill booked' : 'slot-pill';
                    const badgeClass = isBooked ? 'slot-badge slot-badge-booked' : 'slot-badge slot-badge-avail';
                    const badgeText = isBooked ? '<i class="fa-solid fa-lock me-1"></i>Booked' : '<i class="fa-solid fa-check me-1"></i>15 Mins';

                    html += `
                        <div class="${pillClass}" 
                             data-time="${slot.time}" 
                             data-display="${slot.display}"
                             ${isBooked ? 'title="This 15-minute slot is already booked. Choose another available slot or request an Emergency Swap."' : ''}>
                            <div class="slot-time-text">${slot.time}</div>
                            <span class="${badgeClass}">${badgeText}</span>
                        </div>
                    `;
                });
                html += '</div>';
                slotsContainer.innerHTML = html;

                // Re-bind click events on available pills
                document.querySelectorAll('.slot-pill').forEach(pill => {
                    pill.addEventListener('click', () => {
                        const isEmergency = emergencyCheckbox && emergencyCheckbox.checked;
                        const isBooked = pill.classList.contains('booked');

                        if (isBooked && !isEmergency) {
                            alert("This 15-minute slot is already booked! Please select an available slot, or toggle 'Emergency Case' if this is a critical emergency requiring slot preemption/swap.");
                            return;
                        }

                        document.querySelectorAll('.slot-pill').forEach(p => p.classList.remove('active'));
                        pill.classList.add('active');

                        const chosenTime = pill.getAttribute('data-time');
                        const chosenDisplay = pill.getAttribute('data-display');
                        if (selectedSlotInput) selectedSlotInput.value = chosenTime;

                        if (selectedSlotSummary) {
                            if (isBooked && isEmergency) {
                                selectedSlotSummary.innerHTML = `
                                    <div class="alert alert-warning py-2 px-3 mb-0 small">
                                        <i class="fa-solid fa-triangle-exclamation me-1"></i>
                                        <strong>Emergency Swap Target:</strong> Slot <strong>${chosenDisplay}</strong> is currently booked. Submitting will execute an <strong>Emergency Swap</strong>, relocating the current patient to the next free slot.
                                    </div>
                                `;
                            } else {
                                selectedSlotSummary.innerHTML = `
                                    <div class="alert alert-info py-2 px-3 mb-0 small">
                                        <i class="fa-solid fa-clock me-1"></i>
                                        Selected Consultation Slot: <strong>${chosenDisplay}</strong> (Strict 15 Minutes)
                                    </div>
                                `;
                            }
                        }
                    });
                });
            })
            .catch(err => {
                slotsContainer.innerHTML = `<div class="col-12 text-danger p-3">Failed to load slots: ${err.message}</div>`;
            });
    }

    doctorSelect.addEventListener('change', fetchSlots);
    dateInput.addEventListener('change', fetchSlots);

    if (emergencyCheckbox) {
        emergencyCheckbox.addEventListener('change', () => {
            if (emergencyWarning) {
                emergencyWarning.classList.toggle('d-none', !emergencyCheckbox.checked);
            }
        });
    }

    // Trigger initial fetch if doctor preselected
    if (doctorSelect.value && dateInput.value) {
        fetchSlots();
    }
});

/**
 * CarePoint Health Meters Suite (Requirement 7)
 * - Blood Sugar Meter
 * - Cholesterol Meter
 * - Overweight / Underweight BMI Meter
 * - Pulse Rate Meter with Live Pulsating Animation
 */

document.addEventListener('DOMContentLoaded', () => {
    initSugarMeter();
    initCholesterolMeter();
    initBmiMeter();
    initPulseMeter();
});

// Helper: map value between range to angle in degrees (-90 to +90)
function mapToAngle(val, minVal, maxVal) {
    const clamped = Math.max(minVal, Math.min(maxVal, val));
    const ratio = (clamped - minVal) / (maxVal - minVal);
    return -90 + (ratio * 180);
}

/* ========================================================
   1. SUGAR METER (Blood Glucose mg/dL)
   Fasting: <70 Low, 70-99 Normal, 100-125 Pre-diabetic, >=126 Diabetic
   Post-meal: <140 Normal, 140-199 Pre-diabetic, >=200 Diabetic
   ======================================================== */
function initSugarMeter() {
    const input = document.getElementById('sugar_fasting_input');
    const typeSelect = document.getElementById('sugar_type_select');
    const displayVal = document.getElementById('sugar_val_display');
    const needle = document.getElementById('sugar_needle');
    const statusPill = document.getElementById('sugar_status_pill');
    const adviceText = document.getElementById('sugar_advice_text');

    if (!input) return;

    function update() {
        const val = parseFloat(input.value) || 0;
        const isPostMeal = typeSelect && typeSelect.value === 'postprandial';
        if (displayVal) displayVal.textContent = val > 0 ? val : '--';

        let angle = -90;
        let status = 'Normal';
        let statusClass = 'status-normal';
        let advice = 'Blood glucose level within healthy clinical range.';

        if (isPostMeal) {
            angle = mapToAngle(val, 60, 260);
            if (val < 70) {
                status = 'Hypoglycemia (Very Low)';
                statusClass = 'status-danger';
                advice = 'Consume quick-acting fast carbohydrates (fruit juice, glucose tab).';
            } else if (val < 140) {
                status = 'Normal (Post-meal)';
                statusClass = 'status-normal';
                advice = 'Healthy post-meal glycemic response.';
            } else if (val <= 199) {
                status = 'Pre-diabetic Range (140-199 mg/dL)';
                statusClass = 'status-borderline';
                advice = 'Lifestyle intervention recommended: monitor dietary carbs and exercise.';
            } else {
                status = 'Elevated / Diabetic Range (≥200 mg/dL)';
                statusClass = 'status-danger';
                advice = 'Consistent elevated readings warrant HbA1c testing and physician consult.';
            }
        } else {
            // Fasting
            angle = mapToAngle(val, 50, 200);
            if (val < 70) {
                status = 'Hypoglycemia (<70 mg/dL)';
                statusClass = 'status-danger';
                advice = 'Dangerously low fasting glucose. Seek guidance if frequent.';
            } else if (val <= 99) {
                status = 'Optimal Normal (70-99 mg/dL)';
                statusClass = 'status-normal';
                advice = 'Excellent fasting glucose level.';
            } else if (val <= 125) {
                status = 'Pre-diabetes (100-125 mg/dL)';
                statusClass = 'status-borderline';
                advice = 'Impaired fasting glucose. Adopt low-glycemic diet and aerobic exercise.';
            } else {
                status = 'Diabetic Range (≥126 mg/dL)';
                statusClass = 'status-danger';
                advice = 'Fasting glucose indicates diabetes mellitus threshold. Consult an endocrinologist.';
            }
        }

        if (needle) needle.style.transform = `rotate(${angle}deg)`;
        if (statusPill) {
            statusPill.textContent = status;
            statusPill.className = `meter-status-pill ${statusClass}`;
        }
        if (adviceText) adviceText.textContent = advice;
    }

    input.addEventListener('input', update);
    if (typeSelect) typeSelect.addEventListener('change', update);
    update();
}

/* ========================================================
   2. CHOLESTEROL METER (mg/dL)
   Total: <200 Optimal, 200-239 Borderline, >=240 High
   ======================================================== */
function initCholesterolMeter() {
    const input = document.getElementById('cholesterol_total_input');
    const displayVal = document.getElementById('cholesterol_val_display');
    const needle = document.getElementById('cholesterol_needle');
    const statusPill = document.getElementById('cholesterol_status_pill');
    const adviceText = document.getElementById('cholesterol_advice_text');

    if (!input) return;

    function update() {
        const val = parseFloat(input.value) || 0;
        if (displayVal) displayVal.textContent = val > 0 ? val : '--';

        const angle = mapToAngle(val, 120, 320);
        let status = 'Desirable (<200 mg/dL)';
        let statusClass = 'status-normal';
        let advice = 'Optimal cardiovascular lipid profile.';

        if (val < 200) {
            status = 'Desirable (<200 mg/dL)';
            statusClass = 'status-normal';
            advice = 'Healthy lipid profile. Maintain high-fiber diet and active lifestyle.';
        } else if (val <= 239) {
            status = 'Borderline High (200-239 mg/dL)';
            statusClass = 'status-borderline';
            advice = 'Moderate cardiovascular risk. Reduce saturated fats and increase Omega-3 intake.';
        } else {
            status = 'High Risk (≥240 mg/dL)';
            statusClass = 'status-danger';
            advice = 'Elevated atherogenic risk. Lipid panel review with a cardiologist recommended.';
        }

        if (needle) needle.style.transform = `rotate(${angle}deg)`;
        if (statusPill) {
            statusPill.textContent = status;
            statusPill.className = `meter-status-pill ${statusClass}`;
        }
        if (adviceText) adviceText.textContent = advice;
    }

    input.addEventListener('input', update);
    update();
}

/* ========================================================
   3. OVERWEIGHT / UNDERWEIGHT METER (BMI)
   <18.5 Underweight, 18.5-24.9 Normal, 25-29.9 Overweight, >=30 Obese
   ======================================================== */
function initBmiMeter() {
    const weightInput = document.getElementById('weight_kg_input');
    const heightInput = document.getElementById('height_cm_input');
    const bmiDisplay = document.getElementById('bmi_val_display');
    const needle = document.getElementById('bmi_needle');
    const statusPill = document.getElementById('bmi_status_pill');
    const adviceText = document.getElementById('bmi_advice_text');
    const idealWeightDisplay = document.getElementById('ideal_weight_display');

    if (!weightInput || !heightInput) return;

    function update() {
        const weight = parseFloat(weightInput.value) || 0;
        const height = parseFloat(heightInput.value) || 0;

        let bmi = 0;
        if (weight > 0 && height > 0) {
            const heightM = height / 100;
            bmi = parseFloat((weight / (heightM * heightM)).toFixed(1));
        }

        if (bmiDisplay) bmiDisplay.textContent = bmi > 0 ? bmi : '--';

        const angle = mapToAngle(bmi, 14, 40);
        let status = 'Normal Weight (18.5 - 24.9)';
        let statusClass = 'status-normal';
        let advice = 'Healthy weight relative to height.';

        if (bmi === 0) {
            status = 'Enter Height & Weight';
            statusClass = 'status-low';
            advice = 'Provide your height and weight to calculate BMI.';
        } else if (bmi < 18.5) {
            status = 'Underweight (BMI < 18.5)';
            statusClass = 'status-low';
            advice = 'Consider nutrient-dense dietary plan and strength conditioning.';
        } else if (bmi <= 24.9) {
            status = 'Normal Healthy Weight (18.5 - 24.9)';
            statusClass = 'status-normal';
            advice = 'Optimal BMI associated with lowest risk of metabolic disorders.';
        } else if (bmi <= 29.9) {
            status = 'Overweight (25.0 - 29.9)';
            statusClass = 'status-borderline';
            advice = 'Increased strain on joints and heart. Consider 150 min/wk moderate activity.';
        } else {
            status = 'Obese Range (BMI ≥ 30.0)';
            statusClass = 'status-danger';
            advice = 'High cardiovascular and metabolic risk. Clinical weight management suggested.';
        }

        if (height > 0 && idealWeightDisplay) {
            const hM = height / 100;
            const minIdeal = (18.5 * hM * hM).toFixed(1);
            const maxIdeal = (24.9 * hM * hM).toFixed(1);
            idealWeightDisplay.textContent = `${minIdeal} kg - ${maxIdeal} kg`;
        }

        if (needle) needle.style.transform = `rotate(${angle}deg)`;
        if (statusPill) {
            statusPill.textContent = status;
            statusPill.className = `meter-status-pill ${statusClass}`;
        }
        if (adviceText) adviceText.textContent = advice;
    }

    weightInput.addEventListener('input', update);
    heightInput.addEventListener('input', update);
    update();
}

/* ========================================================
   4. PULSE RATE METER (Heart Rate BPM)
   <60 Bradycardia, 60-100 Normal, >100 Tachycardia
   Animates live pulsating heart icon with exact frequency!
   ======================================================== */
function initPulseMeter() {
    const input = document.getElementById('pulse_rate_input');
    const displayVal = document.getElementById('pulse_val_display');
    const needle = document.getElementById('pulse_needle');
    const statusPill = document.getElementById('pulse_status_pill');
    const adviceText = document.getElementById('pulse_advice_text');
    const heartIcon = document.getElementById('pulse_live_heart');

    if (!input) return;

    function update() {
        const bpm = parseInt(input.value, 10) || 72;
        if (displayVal) displayVal.textContent = bpm;

        // Dynamic pulse animation speed: seconds per beat = 60 / bpm
        if (heartIcon) {
            const secondsPerBeat = Math.max(0.3, Math.min(2.0, (60 / Math.max(30, bpm)).toFixed(2)));
            heartIcon.style.animationDuration = `${secondsPerBeat}s`;
        }

        const angle = mapToAngle(bpm, 40, 160);
        let status = 'Normal Resting Heart Rate (60-100 BPM)';
        let statusClass = 'status-normal';
        let advice = 'Normal rhythm and cardiac contraction rate.';

        if (bpm < 60) {
            status = 'Bradycardia (<60 BPM)';
            statusClass = bpm < 50 ? 'status-danger' : 'status-low';
            advice = bpm < 50 ? 'Significantly low resting heart rate. Assess for dizziness or fatigue.' : 'Low resting rate (common in conditioned endurance athletes).';
        } else if (bpm <= 100) {
            status = 'Optimal Normal (60-100 BPM)';
            statusClass = 'status-normal';
            advice = 'Standard physiological sinus rhythm.';
        } else {
            status = 'Tachycardia (>100 BPM)';
            statusClass = bpm > 130 ? 'status-danger' : 'status-borderline';
            advice = 'Elevated heart rate. Check for stress, caffeine, fever, dehydration, or arrhythmia.';
        }

        if (needle) needle.style.transform = `rotate(${angle}deg)`;
        if (statusPill) {
            statusPill.textContent = status;
            statusPill.className = `meter-status-pill ${statusClass}`;
        }
        if (adviceText) adviceText.textContent = advice;
    }

    input.addEventListener('input', update);
    update();
}

// Preset simulator for quick testing
window.applyMeterPreset = function(preset) {
    if (preset === 'healthy') {
        const s = document.getElementById('sugar_fasting_input'); if (s) s.value = 88;
        const c = document.getElementById('cholesterol_total_input'); if (c) c.value = 175;
        const w = document.getElementById('weight_kg_input'); if (w) w.value = 68;
        const h = document.getElementById('height_cm_input'); if (h) h.value = 172;
        const p = document.getElementById('pulse_rate_input'); if (p) p.value = 68;
    } else if (preset === 'high_sugar') {
        const s = document.getElementById('sugar_fasting_input'); if (s) s.value = 142;
        const c = document.getElementById('cholesterol_total_input'); if (c) c.value = 210;
        const w = document.getElementById('weight_kg_input'); if (w) w.value = 84;
        const h = document.getElementById('height_cm_input'); if (h) h.value = 170;
        const p = document.getElementById('pulse_rate_input'); if (p) p.value = 84;
    } else if (preset === 'tachycardia') {
        const p = document.getElementById('pulse_rate_input'); if (p) p.value = 118;
    }
    // Trigger dispatch
    document.querySelectorAll('input').forEach(el => el.dispatchEvent(new Event('input')));
};

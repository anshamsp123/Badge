/**
 * Claim Submission Module - Frontend JavaScript
 * Handles claim submission form and displays results with XAI explanations
 */

// Claim submission functionality
let currentClaimId = null;

function initializeClaimModule() {
    const submitClaimBtn = document.getElementById('submitClaimBtn');
    const claimForm = document.getElementById('claimForm');

    if (submitClaimBtn) {
        submitClaimBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleClaimSubmission();
        });
    }

    if (claimForm) {
        claimForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleClaimSubmission();
        });
    }
}

async function handleClaimSubmission() {
    const policyId = document.getElementById('policyId').value.trim();
    const treatmentType = document.getElementById('treatmentType').value;
    const claimedAmount = parseFloat(document.getElementById('claimedAmount').value);
    const hospitalName = document.getElementById('hospitalName').value.trim();
    const treatmentDate = document.getElementById('treatmentDate').value;
    const description = document.getElementById('claimDescription').value.trim();

    // Validation
    if (!policyId || !claimedAmount || claimedAmount <= 0) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    // Show loading
    showLoading('Processing your claim...');

    // Disable button
    const submitBtn = document.getElementById('submitClaimBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
    }

    try {
        // Add a timeout to the fetch request (30 seconds)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for RAG

        const response = await fetch('/api/claims/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...auth.getHeaders()
            },
            body: JSON.stringify({
                policy_id: policyId,
                treatment_type: treatmentType,
                claimed_amount: claimedAmount,
                hospital_name: hospitalName || null,
                treatment_date: treatmentDate || null,
                description: description || null
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error('Failed to submit claim');
        }

        const decision = await response.json();
        currentClaimId = decision.claim_id;

        // Switch to result view
        document.getElementById('submit-claim-view').classList.remove('active');
        document.getElementById('claim-result-view').classList.add('active');

        // Display decision
        displayClaimDecision(decision);

        showToast('Claim processed successfully!', 'success');

    } catch (error) {
        console.error('Error submitting claim:', error);
        if (error.name === 'AbortError') {
            showToast('Request timed out. The AI is taking longer than expected.', 'error');
        } else {
            showToast('Error submitting claim. Please try again.', 'error');
        }
    } finally {
        hideLoading();
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
        }
    }
}

function showClaimForm() {
    // Switch back to form view
    document.getElementById('claim-result-view').classList.remove('active');
    document.getElementById('submit-claim-view').classList.add('active');

    // Reset form
    document.getElementById('claimForm').reset();
}

function displayClaimDecision(decision) {
    const resultDiv = document.getElementById('claimResultContent');
    const explanation = decision.explanation;

    // Determine status color and icon
    const statusConfig = {
        'approved': { color: '#10b981', icon: '✅', text: 'APPROVED', bg: 'rgba(16, 185, 129, 0.1)' },
        'rejected': { color: '#ef4444', icon: '❌', text: 'REJECTED', bg: 'rgba(239, 68, 68, 0.1)' },
        'under_review': { color: '#f59e0b', icon: '⏳', text: 'UNDER REVIEW', bg: 'rgba(245, 158, 11, 0.1)' }
    };

    const status = statusConfig[decision.decision] || statusConfig['under_review'];

    resultDiv.innerHTML = `
        <!-- Section 1: Decision Overview -->
        <div class="claim-decision-card" style="border-left: 4px solid ${status.color}; margin-bottom: 2rem; background: var(--bg-card); border-radius: 12px; overflow: hidden;">
            <div class="decision-header" style="background: ${status.bg}; padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div class="decision-status" style="color: ${status.color}; font-size: 1.5rem; font-weight: bold; display: flex; align-items: center; gap: 0.5rem;">
                    <span class="status-icon">${status.icon}</span>
                    <span class="status-text">${status.text}</span>
                </div>
                <div class="claim-id" style="margin-top: 0.5rem; color: var(--text-secondary);">Claim ID: ${decision.claim_id}</div>
            </div>
            
            <div class="decision-summary" style="padding: 1.5rem;">
                <div class="summary-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                    <div class="summary-item">
                        <label style="display: block; color: var(--text-secondary); margin-bottom: 0.25rem;">Policy Number</label>
                        <span style="font-weight: 600; font-size: 1.1rem;">${decision.policy_id}</span>
                    </div>
                    <div class="summary-item">
                        <label style="display: block; color: var(--text-secondary); margin-bottom: 0.25rem;">Treatment</label>
                        <span style="font-weight: 600; font-size: 1.1rem;">${decision.treatment_type}</span>
                    </div>
                    <div class="summary-item">
                        <label style="display: block; color: var(--text-secondary); margin-bottom: 0.25rem;">Claimed Amount</label>
                        <span style="font-weight: 600; font-size: 1.1rem;">₹${decision.claimed_amount.toLocaleString('en-IN')}</span>
                    </div>
                    <div class="summary-item">
                        <label style="display: block; color: var(--text-secondary); margin-bottom: 0.25rem;">Approved Amount</label>
                        <span style="color: ${status.color}; font-weight: bold; font-size: 1.2rem;">₹${decision.approved_amount.toLocaleString('en-IN')}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 2: Explainable AI (XAI) Analysis -->
        <div class="xai-section" style="background: var(--bg-card); border-radius: 12px; padding: 2rem; border: 1px solid rgba(255,255,255,0.05);">
            <h3 style="color: var(--primary-solid); margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                <span>🧠</span> Explainable AI Analysis
            </h3>
            
            <div class="explanation-content">
                <div class="reasoning-box" style="background: var(--bg-tertiary); padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 3px solid var(--primary-solid);">
                    <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase;">Why this decision?</h4>
                    <p class="explanation-text" style="font-size: 1.1rem; line-height: 1.6;">${explanation.reason}</p>
                </div>
                
                <div class="analysis-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-bottom: 1.5rem;">
                    <div class="calculation-details">
                        <h4 style="color: var(--text-secondary); margin-bottom: 1rem;">Calculation Breakdown</h4>
                        <div class="calc-grid" style="display: flex; flex-direction: column; gap: 0.75rem;">
                            ${Object.entries(explanation.calculation_details).map(([key, value]) => `
                                <div class="calc-item" style="display: flex; justify-content: space-between; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <span class="calc-label" style="color: var(--text-secondary);">${formatCalculationLabel(key)}</span>
                                    <span class="calc-value" style="font-weight: 600;">${formatCalculationValue(key, value)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    ${explanation.relevant_clauses.length > 0 ? `
                        <div class="policy-clauses">
                            <h4 style="color: var(--text-secondary); margin-bottom: 1rem;">Relevant Policy Clauses</h4>
                            <ul style="list-style: none; padding: 0;">
                                ${explanation.relevant_clauses.map(clause => `
                                    <li style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.95rem; border-left: 3px solid var(--accent);">${clause}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
                
                <div class="confidence-section" style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <div class="confidence-score" style="display: flex; align-items: center; gap: 1rem;">
                        <label style="color: var(--text-secondary);">AI Confidence Score:</label>
                        <div class="confidence-bar" style="flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; max-width: 200px;">
                            <div class="confidence-fill" style="width: ${explanation.confidence_score * 100}%; height: 100%; background-color: ${status.color}"></div>
                        </div>
                        <span style="font-weight: bold; color: ${status.color};">${(explanation.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                </div>
            </div>
            
            <div class="decision-actions" style="margin-top: 2rem; display: flex; gap: 1rem;">
                <button class="btn-secondary" onclick="viewDetailedExplanation('${decision.claim_id}')" style="background: transparent; border: 1px solid var(--primary-solid); color: var(--primary-solid); padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                    View Full Audit Trail
                </button>
                <button class="btn-secondary" onclick="downloadClaimReport('${decision.claim_id}')" style="background: transparent; border: 1px solid var(--text-secondary); color: var(--text-secondary); padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">
                    Download Report
                </button>
            </div>
        </div>
    `;

    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

async function viewDetailedExplanation(claimId) {
    showLoading('Loading detailed explanation...');

    try {
        const response = await fetch(`/api/claims/${claimId}/explanation`);
        if (!response.ok) throw new Error('Failed to fetch explanation');

        const explanation = await response.json();
        displayDetailedExplanation(explanation);

    } catch (error) {
        console.error('Error fetching explanation:', error);
        showToast('Error loading explanation', 'error');
    } finally {
        hideLoading();
    }
}

function displayDetailedExplanation(explanation) {
    // Create modal or new section for detailed explanation
    const modal = document.createElement('div');
    modal.className = 'explanation-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Detailed Claim Explanation</h2>
                <button class="close-btn" onclick="this.closest('.explanation-modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <div class="explanation-section">
                    <h3>${explanation.decision_summary}</h3>
                </div>
                
                <div class="explanation-section">
                    <h4>Reasoning:</h4>
                    <p>${explanation.reasoning.primary_reason}</p>
                    
                    ${explanation.reasoning.decision_factors.length > 0 ? `
                        <div class="factors-list">
                            ${explanation.reasoning.decision_factors.map(factor => `
                                <div class="factor-item">
                                    <strong>${factor.factor}:</strong> ${factor.value}
                                    <p class="factor-desc">${factor.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                
                <div class="explanation-section">
                    <h4>Next Steps:</h4>
                    <ol>
                        ${explanation.next_steps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                </div>
                
                ${explanation.audit_trail ? `
                    <div class="explanation-section">
                        <h4>Audit Trail:</h4>
                        <pre>${JSON.stringify(explanation.audit_trail, null, 2)}</pre>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function formatCalculationLabel(key) {
    const labels = {
        'coverage_limit': 'Coverage Limit',
        'claimed_amount': 'Claimed Amount',
        'threshold_amount': 'Approval Threshold',
        'percentage_of_limit': 'Percentage of Coverage',
        'fraud_risk_score': 'Fraud Risk Score',
        'fraud_risk_level': 'Fraud Risk Level'
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatCalculationValue(key, value) {
    if (key.includes('amount') || key.includes('limit')) {
        return `₹${value.toLocaleString('en-IN')}`;
    } else if (key.includes('percentage')) {
        return `${value.toFixed(1)}%`;
    }
    return value;
}

function downloadClaimReport(claimId) {
    // In a real implementation, this would generate a PDF
    showToast('Report download feature coming soon!', 'info');
}

// ==================== Utility Functions ====================
function showLoading(message = 'Processing...') {
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    if (loadingOverlay) {
        if (loadingText) {
            loadingText.textContent = message;
        }
        loadingOverlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeClaimModule);
} else {
    initializeClaimModule();
}

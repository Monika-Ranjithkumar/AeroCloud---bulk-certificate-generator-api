let currentJobId = null;
let currentCertificates = [];

const THEME_STYLES = {
  classic_gold: {
    primary: "#1E3A8A",
    secondary: "#D97706",
    textDark: "#0F172A",
    textMuted: "#475569",
    line: "#CBD5E1",
    bg: "#FFFFFF",
    tag: "Classic Gold"
  },
  modern_emerald: {
    primary: "#065F46",
    secondary: "#10B981",
    textDark: "#022C22",
    textMuted: "#047857",
    line: "#A7F3D0",
    bg: "#F0FDF4",
    tag: "Modern Emerald"
  },
  executive_crimson: {
    primary: "#881337",
    secondary: "#D97706",
    textDark: "#4C0519",
    textMuted: "#9F1239",
    line: "#FECDD3",
    bg: "#FFF1F2",
    tag: "Executive Crimson"
  },
  minimalist_purple: {
    primary: "#4C1D95",
    secondary: "#8B5CF6",
    textDark: "#1E1B4B",
    textMuted: "#6D28D9",
    line: "#DDD6FE",
    bg: "#F5F3FF",
    tag: "Minimalist Violet"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("issue-date").value = today;
  updateLivePreview();
});

function switchTab(tabName) {
  document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-view").forEach(view => view.classList.remove("active"));

  document.getElementById(`tab-${tabName}`).classList.add("active");
  document.getElementById(`view-${tabName}`).classList.add("active");
}

function updateLivePreview() {
  const templateId = document.getElementById("template-select")?.value || "classic_gold";
  const theme = THEME_STYLES[templateId] || THEME_STYLES["classic_gold"];

  const issuer = document.getElementById("issuer-name").value || "AeroCloud Academy";
  const title = document.getElementById("cert-title").value || "CERTIFICATE OF ACHIEVEMENT";
  const course = document.getElementById("course-title").value || "Course Title Here";
  const date = document.getElementById("issue-date").value || "2026-10-10";
  
  const recipientsText = document.getElementById("recipients-text").value.trim();
  let firstRecipient = "Sarah Connor";
  if (recipientsText) {
    const firstLine = recipientsText.split("\n")[0];
    if (firstLine.includes(",")) {
      firstRecipient = firstLine.split(",")[0].trim();
    } else if (firstLine.trim()) {
      firstRecipient = firstLine.trim();
    }
  }

  // Update Text Contents
  document.getElementById("preview-issuer").innerText = issuer.toUpperCase();
  document.getElementById("preview-title").innerText = title.toUpperCase();
  document.getElementById("preview-course").innerText = course;
  document.getElementById("preview-name").innerText = firstRecipient;
  document.getElementById("preview-date").innerText = date;
  document.getElementById("preview-sig").innerText = issuer;
  document.getElementById("preview-theme-tag").innerText = theme.tag;

  // Apply Live Theme Styling to Preview Box
  document.getElementById("preview-outer-border").style.borderColor = theme.primary;
  document.getElementById("preview-inner-border").style.borderColor = theme.secondary;
  document.getElementById("preview-inner-border").style.backgroundColor = theme.bg;

  document.getElementById("preview-issuer").style.color = theme.primary;
  document.getElementById("preview-title").style.color = theme.textDark;
  document.getElementById("preview-line-1").style.backgroundColor = theme.secondary;
  document.getElementById("preview-sub").style.color = theme.textMuted;
  document.getElementById("preview-name").style.color = theme.primary;
  document.getElementById("preview-line-2").style.backgroundColor = theme.line;
  document.getElementById("preview-body").style.color = theme.textMuted;
  document.getElementById("preview-course").style.color = theme.textDark;
  document.getElementById("preview-date").style.color = theme.textDark;
  document.getElementById("preview-sig").style.color = theme.primary;
}

function loadSampleParticipants() {
  const sampleList = [
    "Alice Johnson, alice@example.com",
    "Bob Smith, bob@example.com",
    "Charlie Brown, charlie@example.com",
    "Diana Prince, diana@example.com"
  ].join("\n");

  document.getElementById("recipients-text").value = sampleList;
  updateLivePreview();
}

async function generateBatch() {
  const templateId = document.getElementById("template-select")?.value || "classic_gold";
  const sendEmail = document.getElementById("send-email-checkbox")?.checked || false;
  const issuer = document.getElementById("issuer-name").value.trim();
  const course = document.getElementById("course-title").value.trim();
  const issueDate = document.getElementById("issue-date").value;
  const rawText = document.getElementById("recipients-text").value.trim();

  if (!rawText) {
    alert("Please enter at least one participant (Name, Email).");
    return;
  }

  const lines = rawText.split("\n");
  const recipients = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    let name = line;
    let email = `participant${i+1}@example.com`;

    if (line.includes(",")) {
      const parts = line.split(",");
      name = parts[0].trim();
      email = parts[1].trim();
    }

    recipients.push({
      name: name,
      email: email,
      identifier: `ID-${1000 + i}`
    });
  }

  const payload = {
    title: `${course} Certification Batch`,
    issuer_name: issuer,
    course_or_event: course,
    issue_date: issueDate,
    template_id: templateId,
    send_email: sendEmail,
    recipients: recipients
  };

  const btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.innerText = "⏳ Generating & Emailing Certificates...";

  try {
    const response = await fetch("/api/v1/jobs?process_async=false", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Failed to create batch job.");
    }

    const jobResult = await response.json();
    currentJobId = jobResult.id;

    // Fetch detailed results
    await loadJobDetails(currentJobId);
    
    // Switch to gallery view
    switchTab("gallery");

  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.innerText = "✨ Generate All Certificates Now";
  }
}

async function loadJobDetails(jobId) {
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}/details`);
    if (!res.ok) return;

    const data = await res.json();
    currentCertificates = data.successful_certificates || [];

    document.getElementById("gallery-subtitle").innerText = 
      `Batch Job: ${data.job.title} | ${data.job.successful_count} Generated Successfully`;
    
    document.getElementById("cert-count-badge").innerText = currentCertificates.length;
    document.getElementById("gallery-actions-bar").style.display = "block";

    renderCertificatesTable(data.successful_certificates, data.failed_certificates);

  } catch (err) {
    console.error("Failed to fetch job details:", err);
  }
}

function renderCertificatesTable(successful, failed) {
  const tbody = document.getElementById("certificates-table-body");
  tbody.innerHTML = "";

  const allItems = [...(successful || []), ...(failed || [])];

  if (allItems.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="empty-state">
          <div class="empty-icon">📜</div>
          <p>No certificates found.</p>
        </td>
      </tr>`;
    return;
  }

  allItems.forEach(cert => {
    const tr = document.createElement("tr");
    const isGenerated = cert.status === "generated";

    tr.innerHTML = `
      <td><strong>${escapeHtml(cert.recipient_name)}</strong></td>
      <td>${escapeHtml(cert.recipient_email)}</td>
      <td><code>${cert.certificate_code || "N/A"}</code></td>
      <td>
        <span class="badge" style="background:${isGenerated ? '#D1FAE5' : '#FEE2E2'}; color:${isGenerated ? '#065F46' : '#991B1B'};">
          ${isGenerated ? '✓ Generated' : '✗ Failed'}
        </span>
      </td>
      <td>
        <span class="badge" style="background:${cert.email_sent ? '#DBEAFE' : '#F1F5F9'}; color:${cert.email_sent ? '#1E40AF' : '#64748B'};">
          ${cert.email_sent ? '📧 Sent' : '➖ Off'}
        </span>
      </td>
      <td class="text-right">
        <div class="action-btn-group">
          ${isGenerated ? `
            <button class="btn-sm" onclick="openPreviewModal('${cert.id}', '${escapeHtml(cert.recipient_name)}')">👁️ Preview</button>
            <a href="/api/v1/certificates/${cert.id}/download" download class="btn-sm" style="text-decoration:none;">📥 PDF</a>
            <button class="btn-sm" onclick="quickVerify('${cert.certificate_code}')">🔍 Verify</button>
          ` : `
            <span style="font-size:12px; color:#DC2626;">${escapeHtml(cert.error_message || 'Error')}</span>
          `}
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function downloadBatchZip() {
  if (!currentJobId) return;
  window.location.href = `/api/v1/jobs/${currentJobId}/download-zip`;
}

function openPreviewModal(certId, recipientName) {
  const modal = document.getElementById("preview-modal");
  const modalImg = document.getElementById("modal-img");
  const modalTitle = document.getElementById("modal-title");

  modalTitle.innerText = `Certificate Preview - ${recipientName}`;
  modalImg.src = `/api/v1/certificates/${certId}/preview`;
  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("preview-modal").classList.remove("active");
}

function quickVerify(code) {
  switchTab("verify");
  document.getElementById("verify-code-input").value = code;
  verifyCertificateCode();
}

async function verifyCertificateCode() {
  const code = document.getElementById("verify-code-input").value.trim();
  if (!code) return;

  const resultBox = document.getElementById("verify-result-box");
  resultBox.style.display = "block";
  resultBox.className = "verify-result-box";
  resultBox.innerHTML = "<p>Verifying certificate...</p>";

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (data.valid) {
      resultBox.className = "verify-result-box valid";
      resultBox.innerHTML = `
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
          <span style="font-size:32px;">✅</span>
          <div>
            <h3 style="color:#065F46;">Authentic & Valid Certificate</h3>
            <p style="font-size:13px; color:#047857;">Issued by ${escapeHtml(data.issuer_name)}</p>
          </div>
        </div>
        <div style="font-size:14px; line-height:1.8;">
          <p><strong>Certificate Code:</strong> <code>${data.certificate_code}</code></p>
          <p><strong>Recipient:</strong> ${escapeHtml(data.recipient_name)}</p>
          <p><strong>Course / Event:</strong> ${escapeHtml(data.course_or_event)}</p>
          <p><strong>Issue Date:</strong> ${escapeHtml(data.issue_date)}</p>
        </div>
      `;
    } else {
      resultBox.className = "verify-result-box invalid";
      resultBox.innerHTML = `
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="font-size:32px;">❌</span>
          <div>
            <h3 style="color:#991B1B;">Invalid Certificate Code</h3>
            <p style="font-size:13px; color:#B91C1C;">${escapeHtml(data.message)}</p>
          </div>
        </div>
      `;
    }
  } catch (err) {
    resultBox.className = "verify-result-box invalid";
    resultBox.innerHTML = `<p style="color:#991B1B;">Verification request failed. Make sure the server is running.</p>`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

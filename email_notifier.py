"""
Email notification module for Lazarus.
Sends decommission report emails to stakeholders via Gmail SMTP.

SETUP:
  1. Go to https://myaccount.google.com/apppasswords
  2. Generate an App Password for "Lazarus"
  3. Paste the 16-char password below in GMAIL_APP_PASSWORD
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Gmail Configuration ──
GMAIL_ADDRESS = "daxketkar10@gmail.com"
GMAIL_APP_PASSWORD = "tntkxvytibcrutuu"  # App Password for Lazarus
RECIPIENT = "daxketkar10@gmail.com"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_decommission_email(decommission_data: dict) -> dict:
    """
    Send a decommission notification email with full audit details.
    Returns a dict with status and details.
    """
    path = decommission_data.get("path", "unknown")
    api_id = decommission_data.get("api_id", "unknown")
    reason = decommission_data.get("reason", "Security risk")
    initiated_at = decommission_data.get("initiated_at", datetime.utcnow().isoformat())
    operator = decommission_data.get("operator", "admin@lazarus")
    steps = decommission_data.get("steps_completed", [])
    verification = decommission_data.get("post_verification", {})
    compliance = decommission_data.get("compliance_summary", {})

    # Build HTML email body
    steps_html = ""
    for step in steps:
        if isinstance(step, dict):
            steps_html += f"""
            <tr>
                <td style="padding:8px 12px; border-bottom:1px solid #e2e8f0; font-size:13px;">
                    <strong>{step.get('action', '')}</strong><br>
                    <span style="color:#64748b; font-size:11px;">{step.get('detail', '')}</span>
                </td>
                <td style="padding:8px 12px; border-bottom:1px solid #e2e8f0; text-align:center;">
                    <span style="background:#f0fdf4; color:#16a34a; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700;">
                        {step.get('status', 'success').upper()}
                    </span>
                </td>
            </tr>"""
        else:
            steps_html += f"""
            <tr>
                <td style="padding:8px 12px; border-bottom:1px solid #e2e8f0; font-size:13px;">{step}</td>
                <td style="padding:8px 12px; border-bottom:1px solid #e2e8f0; text-align:center;">
                    <span style="background:#f0fdf4; color:#16a34a; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700;">SUCCESS</span>
                </td>
            </tr>"""

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width:640px; margin:0 auto; background:#f8fafc; padding:24px;">
        <div style="background:#1e293b; color:white; padding:20px 24px; border-radius:12px 12px 0 0;">
            <h1 style="margin:0; font-size:18px;">🔒 Lazarus — API Decommission Report</h1>
            <p style="margin:4px 0 0; font-size:12px; color:#94a3b8;">Zombie API Discovery & Defence Platform</p>
        </div>

        <div style="background:white; padding:24px; border:1px solid #e2e8f0; border-top:none;">
            <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:16px; margin-bottom:20px;">
                <h2 style="margin:0 0 8px; font-size:15px; color:#dc2626;">⚠ API Decommissioned</h2>
                <p style="margin:0; font-size:13px; color:#475569;">
                    The following API has been identified as a security risk and has been decommissioned.
                </p>
            </div>

            <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b; width:120px;">API Path</td>
                    <td style="padding:6px 0; font-size:13px; font-weight:600;"><code>{path}</code></td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">API ID</td>
                    <td style="padding:6px 0; font-size:13px; font-weight:600;">{api_id}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Reason</td>
                    <td style="padding:6px 0; font-size:13px;">{reason}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Operator</td>
                    <td style="padding:6px 0; font-size:13px;">{operator}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Initiated</td>
                    <td style="padding:6px 0; font-size:13px;">{initiated_at}</td>
                </tr>
            </table>

            <h3 style="font-size:14px; color:#1e293b; margin:20px 0 10px; border-bottom:1px solid #e2e8f0; padding-bottom:8px;">
                📋 Execution Audit Trail
            </h3>
            <table style="width:100%; border-collapse:collapse;">
                {steps_html}
            </table>

            <h3 style="font-size:14px; color:#1e293b; margin:20px 0 10px; border-bottom:1px solid #e2e8f0; padding-bottom:8px;">
                ✅ Post-Decommission Verification
            </h3>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Endpoint Status</td>
                    <td style="padding:6px 0; font-size:13px; font-weight:600; color:#16a34a;">{verification.get('endpoint_status', 'BLOCKED')}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">DNS Resolved</td>
                    <td style="padding:6px 0; font-size:13px;">{'❌ Still Active' if verification.get('dns_resolved') else '✅ Removed'}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Tokens Revoked</td>
                    <td style="padding:6px 0; font-size:13px;">{verification.get('tokens_revoked', 0):,} tokens invalidated</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Gateway Rule</td>
                    <td style="padding:6px 0; font-size:13px;">{'✅ Active' if verification.get('gateway_rule_active') else '❌ Inactive'}</td>
                </tr>
            </table>

            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px; margin:16px 0; text-align:center;">
                <strong style="color:#16a34a; font-size:13px;">
                    🛡 {verification.get('result', 'VERIFIED — Endpoint is fully decommissioned')}
                </strong>
            </div>

            <h3 style="font-size:14px; color:#1e293b; margin:20px 0 10px; border-bottom:1px solid #e2e8f0; padding-bottom:8px;">
                📜 Compliance Summary
            </h3>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Regulation</td>
                    <td style="padding:6px 0; font-size:13px;">{compliance.get('regulation', 'RBI / PCI-DSS')}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Risk Before</td>
                    <td style="padding:6px 0; font-size:13px; color:#dc2626; font-weight:600;">{compliance.get('risk_before', 'CRITICAL')}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Risk After</td>
                    <td style="padding:6px 0; font-size:13px; color:#16a34a; font-weight:600;">{compliance.get('risk_after', 'REMEDIATED')}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; font-size:12px; color:#64748b;">Audit Ready</td>
                    <td style="padding:6px 0; font-size:13px; color:#16a34a; font-weight:600;">{'✅ Yes' if compliance.get('audit_ready') else '❌ No'}</td>
                </tr>
            </table>
        </div>

        <div style="background:#f1f5f9; padding:16px 24px; border-radius:0 0 12px 12px; border:1px solid #e2e8f0; border-top:none; text-align:center;">
            <p style="margin:0; font-size:11px; color:#94a3b8;">
                This is an automated report from Lazarus — Zombie API Discovery & Defence Platform<br>
                Generated at {datetime.utcnow().isoformat()}Z
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔒 [Lazarus] API Decommissioned: {path}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    result = {
        "recipient": RECIPIENT,
        "subject": msg["Subject"],
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if not GMAIL_APP_PASSWORD:
        result["status"] = "skipped"
        result["error"] = "No Gmail App Password configured. Set GMAIL_APP_PASSWORD in email_notifier.py"
        print(f"[EMAIL] ⚠ Skipped — no App Password set. See email_notifier.py line 18.")
        return result

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [RECIPIENT], msg.as_string())
        result["status"] = "delivered"
        print(f"[EMAIL] ✅ Sent decommission report to {RECIPIENT}")
    except smtplib.SMTPAuthenticationError:
        result["status"] = "auth_failed"
        result["error"] = "Gmail rejected the App Password. Regenerate it at https://myaccount.google.com/apppasswords"
        print(f"[EMAIL] ❌ Authentication failed. Check your App Password.")
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        print(f"[EMAIL] ⚠ Could not send email: {e}")

    return result

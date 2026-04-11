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

    incident_id = decommission_data.get("incident_id", f"INC-{int(datetime.utcnow().timestamp())}")
    method = decommission_data.get("method", "ANY")
    env = decommission_data.get("environment", "Production / External Edge")

    # Build HTML email body
    steps_html = ""
    for step in steps:
        if isinstance(step, dict):
            steps_html += f"""
            <tr>
                <td style="padding:12px; border-bottom:1px solid #f1f5f9; font-size:14px; color:#334155;">
                    <strong style="color:#0f172a;">{step.get('action', '')}</strong><br>
                    <span style="color:#64748b; font-size:12px; line-height:1.4; display:block; margin-top:2px;">{step.get('detail', '')}</span>
                </td>
                <td style="padding:12px; border-bottom:1px solid #f1f5f9; text-align:right; width:100px;">
                    <span style="background:#dcfce7; color:#166534; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700; display:inline-block;">
                        {step.get('status', 'SUCCESS').upper()}
                    </span>
                </td>
            </tr>"""
        else:
            steps_html += f"""
            <tr>
                <td style="padding:12px; border-bottom:1px solid #f1f5f9; font-size:14px; color:#334155;">{step}</td>
                <td style="padding:12px; border-bottom:1px solid #f1f5f9; text-align:right; width:100px;">
                    <span style="background:#dcfce7; color:#166534; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700; display:inline-block;">SUCCESS</span>
                </td>
            </tr>"""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f8fafc; -webkit-font-smoothing:antialiased;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:680px; margin:0 auto; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <tr>
                <td style="padding:32px 16px;">
                    <!-- Main Card -->
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background:#ffffff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; box-shadow:0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding:36px 32px; text-align:center;">
                                <div style="font-size:36px; margin-bottom:12px; line-height:1;">🚨</div>
                                <h1 style="margin:0 0 6px; font-size:24px; font-weight:700; color:#ffffff; letter-spacing:-0.02em;">Lazarus Intervention Report</h1>
                                <p style="margin:0; font-size:14px; color:#94a3b8; font-weight:500;">Automated Kill-Switch Executed</p>
                            </td>
                        </tr>

                        <!-- Banner -->
                        <tr>
                            <td style="background:#fef2f2; border-bottom:1px solid #fee2e2; padding:16px 32px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="color:#b91c1c; font-size:14px; font-weight:700;">STATUS: THREAT NEUTRALIZED</td>
                                        <td style="text-align:right;"><span style="color:#ef4444; font-size:12px; font-weight:700; background:#fee2e2; padding:4px 10px; border-radius:16px; border:1px solid #fca5a5;">ID: {incident_id}</span></td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Body Content -->
                        <tr>
                            <td style="padding:32px;">
                                <h2 style="margin:0 0 16px; font-size:16px; color:#0f172a; text-transform:uppercase; letter-spacing:0.05em;">Target Profile</h2>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background:#f8fafc; border-radius:8px; padding:16px; margin-bottom:32px; border:1px solid #f1f5f9;">
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b; width:120px;">Environment</td>
                                        <td style="padding:8px; font-size:14px; font-weight:600; color:#0f172a;">{env}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b;">Endpoint Path</td>
                                        <td style="padding:8px; font-size:14px; font-weight:700; color:#2563eb; word-break:break-all;">[{method}] {path}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b;">API ID</td>
                                        <td style="padding:8px; font-size:14px; font-family:monospace; color:#475569;">{api_id}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b;">Termination Reason</td>
                                        <td style="padding:8px; font-size:14px; font-weight:500; color:#dc2626;">{reason}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b;">Initiator</td>
                                        <td style="padding:8px; font-size:14px; font-weight:500; color:#0f172a;">{operator}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px; font-size:13px; color:#64748b;">Timestamp</td>
                                        <td style="padding:8px; font-size:14px; font-weight:500; color:#0f172a;">{initiated_at}Z</td>
                                    </tr>
                                </table>

                                <h2 style="margin:0 0 12px; font-size:16px; color:#0f172a; text-transform:uppercase; letter-spacing:0.05em;">Execution Audit Trail</h2>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:32px;">
                                    {steps_html}
                                </table>

                                <h2 style="margin:0 0 12px; font-size:16px; color:#0f172a; text-transform:uppercase; letter-spacing:0.05em;">Post-Event Verification</h2>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:24px;">
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Endpoint Reachability</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:700; color:#16a34a; text-align:right;">{verification.get('endpoint_status', 'BLOCKED - HTTP 403')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">DNS Resolution Check</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:600; color:#0f172a; text-align:right;">{'❌ Still Resolving' if verification.get('dns_resolved') else '✅ Entry Purged (NXDOMAIN)'}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Token Revocation Check</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:600; color:#0f172a; text-align:right;">{verification.get('tokens_revoked', 0):,} access tokens invalidated</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Gateway Kong Rule</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:600; color:#0f172a; text-align:right;">{'✅ Intercept Applied' if verification.get('gateway_rule_active') else '❌ Intercept Missing'}</td>
                                    </tr>
                                </table>

                                
                                <h2 style="margin:0 0 12px; font-size:16px; color:#0f172a; text-transform:uppercase; letter-spacing:0.05em;">Compliance Posture</h2>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Framework</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:600; color:#0f172a; text-align:right;">{compliance.get('regulation', 'RBI / PCI-DSS / GDPR')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Risk Posture (Pre-Action)</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:700; color:#dc2626; text-align:right;">{compliance.get('risk_before', 'CRITICAL / DATA EXPOSURE')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#64748b;">Risk Posture (Post-Action)</td>
                                        <td style="padding:10px 0; border-bottom:1px solid #f1f5f9; font-size:13px; font-weight:700; color:#16a34a; text-align:right;">{compliance.get('risk_after', 'REMEDIATED / SECURE')}</td>
                                    </tr>
                                </table>

                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc; padding:24px 32px; border-top:1px solid #e2e8f0; text-align:center;">
                                <div style="display:inline-block; padding:8px 16px; background:#e2e8f0; border-radius:100px; color:#475569; font-size:12px; font-weight:600; letter-spacing:0.05em; margin-bottom:16px;">
                                    {verification.get('result', 'SYSTEM FULLY SECURED 🛡️')}
                                </div>
                                <p style="margin:0; font-size:12px; color:#64748b; line-height:1.5;">
                                    This is an automatically generated intervention report from the<br>
                                    <strong>Lazarus Adaptive API Defence Platform</strong>.<br>
                                    <span style="font-size:11px; color:#94a3b8; margin-top:8px; display:block;">Report Generated: {datetime.utcnow().isoformat()}Z</span>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
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

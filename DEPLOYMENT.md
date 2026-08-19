# Real-World Deployment Notes

This project was deployed and tested in an **offline, air-gapped environment** (no internet access), simulating a realistic high-security organizational setting. This document summarizes the deployment process, the technical challenges encountered, and how each was resolved — intended as both a practical guide and a record of real production-adjacent experience beyond local development.

---

## Deployment Environment

- Windows Server, LAN-connected, **no internet access**
- Enterprise endpoint security software (Kaspersky Endpoint Security) active and centrally managed
- No pre-installed development tools (no VS Code, no Git initially)

---

## 1. Offline Installation Strategy

Since the target server has no internet access, all dependencies were prepared on a separate internet-connected machine first, then transferred via USB:

- **Python**: downloaded the official 64-bit Windows installer (`.exe`) — a single self-contained file, no internet needed during install
- **MySQL**: downloaded the full offline MSI/ZIP installer (not the smaller "web installer," which requires internet during setup)
- **Python libraries**: downloaded as `.whl` files using:

pip download -r requirements.txt -d offline_packages

  then installed offline using:

pip install --no-index --find-links=offline_packages -r requirements.txt

- **NLTK stopword data**: downloaded separately (`nltk.download("stopwords")` on a connected machine) and manually copied to `%AppData%\Roaming\nltk_data` on the offline machine, since this data is not distributed via pip

**Key lesson:** `pip download` and `pip install` are distinct actions — some data dependencies (like NLTK corpora) are not part of the pip package itself and must be transferred separately.

---

## 2. MySQL Version Compatibility

An initial MySQL installation turned out to be a legacy version (5.6), which uses a different initialization process (`mysql_install_db.exe`) than modern MySQL (8.0, which uses `mysqld --initialize`). This was identified via:

mysqld --version

and resolved by re-downloading the correct current version (8.0.x) and reinstalling.

**Key lesson:** always verify the exact version of a downloaded installer before deploying — download pages can default to older archived releases.

---

## 3. Authentication Quirk: `localhost` vs `127.0.0.1`

The MySQL command-line client failed to authenticate using the default `localhost` connection, while MySQL Workbench succeeded using `127.0.0.1`. This was resolved by explicitly specifying the TCP/IP connection method:

mysql -h 127.0.0.1 -P 3306 -u root -p


**Key lesson:** on Windows, MySQL clients may default to different connection methods (named pipe vs. TCP/IP), which can behave inconsistently across tools even when pointing to the same server.

---

## 4. False-Positive Security Block (NLTK Import Security)

A newer NLTK release includes a built-in security feature (`nltk/inisec.py`) that blocks module imports resolving to the current working directory, to mitigate a known vulnerability class (CWE-427, uncontrolled search path). This was triggered as a false positive because Python was launched from `C:\Users\<user>`, which is a parent directory of the Python installation itself (`...\AppData\Local\Programs\Python\`) — causing NLTK to treat the legitimate standard-library `locale` module as a potential CWD-shadowing risk.

**Resolution:** running Python from the actual project directory (not the user's home folder) avoided the false trigger entirely.

**Key lesson:** always run project scripts from within the project directory, not from a parent or unrelated folder — this avoids incidental path-shadowing issues with security-conscious libraries.

---

## 5. Enterprise Endpoint Security Interference

Kaspersky Endpoint Security's **Self-Defense** feature blocked the browser (Chrome) from maintaining the live WebSocket connection required by the Streamlit dashboard, despite no related entries appearing in standard antivirus scan logs — the block was only visible in the **System Audit** event log, logged as a restricted resource access event.

**Resolution path (requires IT/security team involvement):**
- Request a Self-Defense / Trusted Application exclusion for `python.exe` and the browser used, specifically for local connections on the Streamlit port (default 8501)
- This is a centrally managed policy in enterprise environments and cannot be resolved by a standard user

**Interim workaround used:** generated a static HTML export of key dashboard charts (via Plotly's `to_html()`) as a fallback that does not require a persistent server connection, allowing results to be viewed while the permanent fix was pending IT approval.

**Key lesson:** enterprise security software can interfere with legitimate local development tools at the network layer, not just the file-scanning layer. Diagnosis required checking multiple distinct log categories (real-time scan, application control, system audit) before the actual cause was identified.

---

## 6. Integration Path for a .NET-Based Organization

Since the target organization's existing systems run on .NET (not Python), the following integration approaches were evaluated:

| Approach | Live/Instant? | Touches Existing Servers? | Effort |
|---|---|---|---|
| External hosted Python API, called by .NET | Yes | No | Low |
| Offline batch file processing (CSV export/import) | No (periodic) | No | Low |
| Native rebuild using ML.NET (no Python at all) | Yes | N/A (built natively) | High |

For a fully air-gapped environment specifically, **batch file processing** was determined to be the most realistic approach: complaint data is periodically exported from the live system as a CSV, physically transferred to the offline environment, and loaded via this project's pipeline (`src/01_load_to_mysql.py` onward).

---

## 7. Hardware Footprint (as deployed)

| Configuration | RAM | Disk | GPU Required? |
|---|---|---|---|
| Lightweight (VADER sentiment, no Transformer model) | ~1–1.5 GB | ~2–3 GB | No |
| Full (includes Transformer-based sentiment model) | ~3–4 GB | ~5–6 GB | No |

No GPU is required at this project's data scale — a graphics card would only become relevant at very high real-time processing volumes or when training new large models from scratch, neither of which applies here.

---

## Summary

Deploying a Python-based ML pipeline into a locked-down, offline, enterprise-secured Windows environment surfaced several real infrastructure challenges beyond the core data science work: dependency packaging, version compatibility, authentication configuration, and — most notably — diagnosing and working around active enterprise security software. Each issue was traced to a specific, verifiable root cause rather than resolved by trial and error, and each has a documented, repeatable fix above.
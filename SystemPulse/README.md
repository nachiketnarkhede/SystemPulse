# SystemPulse

Local-first system intelligence platform.

Included: responsive browser dashboard, Python psutil agent, CPU/RAM/disk/network telemetry, Windows Wi-Fi and device collection, process snapshots, event timeline, Agent L evidence-based reasoning, research sessions with CSV export, JSON reports, PWA shell, and Netlify-ready frontend/function scaffold.

Run locally:

    pip install -r requirements.txt
    python server.py

Open http://127.0.0.1:8000

Netlify can host the `web` frontend. Hardware/process telemetry requires the local Python agent; a normal browser cannot freely inspect another device's internals. Do not expose the local agent publicly without authentication, pairing, HTTPS, and explicit telemetry consent.

Security philosophy: observation -> evidence -> assessment -> recommendation. An anomaly or listening port is not automatically a vulnerability.

## Product Metadata

**SystemPulse** is developed by **Avyakta NX Systems**.

- Product: SystemPulse
- Developer: Avyakta NX Systems
- Architecture: Local-first system intelligence
- Interface: Browser-based
- Local agent: Python
- Cloud dependency for machine telemetry: None

This attribution identifies the product developer and does not change telemetry or analysis behavior.

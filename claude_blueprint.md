# Implementation Blueprint for Claude: Humanized, Top-Notch CRM Redesign

This blueprint details the exact technical and aesthetic changes required to transition the Digital FTE CRM from a "futuristic/cyber" aesthetic to a warm, elegant, "humanized" enterprise system, while strictly enforcing the "no placeholders, 100% real data" constraint.

**Instruction for Claude**: Implement the following changes across the stack. Ensure the outcome is a high-end, flawlessly smooth application.

## 1. Aesthetic Pivot: "Warm, Elegant, & Humanized"
The user requests a design that "feels like home", is highly welcoming, but remains extremely professional ("top-notch high standard"). 
*   **Action**: Completely overhaul `frontend/src/styles/globals.css`.
*   **Color Palette**: Move away from deep black backgrounds and neon cyan/magenta gradients. Implement a light, airy, and warm theme.
    *   Backgrounds: Soft warm off-whites (e.g., `#FAFAFA` or `#FDFDFD`).
    *   Surfaces: Pure white (`#FFFFFF`) with subtle, diffuse drop shadows (no neon glows).
    *   Accents: Muted, elegant tones like Sage Green, soft Terracotta, or refined Navy Blue.
*   **Typography**: Ensure clean, elegant sans-serif fonts (like Inter or Plus Jakarta Sans) are used. Remove any harsh monospace styling from primary headers.
*   **Background Image**: A new asset has been generated and placed at `frontend/public/elegant-human-bg.png`. Update the landing page hero section in `frontend/src/pages/index.js` to use this image as a subtle, sophisticated background layer rather than the dark "starfield/orb" styling.

## 2. Reframing the Copywriting
Eliminate robotic, sci-fi terminology ("Neural Ingestion Matrix", "Payload", "Protocol", "Agent M"). The phrasing should be exceptionally professional and human-centric, without being overly casual.
*   **Landing Page (`frontend/src/pages/index.js`)**: 
    *   Change "Support That Actually Thinks" to something like "An Extension of Your Team."
    *   Change form labels from "IDENTIFIER" and "MESSAGE PAYLOAD" to standard, elegant labels ("Full Name", "How can we help?").
*   **Dashboard (`frontend/src/pages/dashboard/index.js`)**:
    *   Remove phrases like "Living Agent Activity Feed" -> Replace with "System Audit Log" or "Recent Team Activity".

## 3. Strict Constraint: 100% Real Data (No Mockups)
Currently, the frontend dashboard uses `stats` counts to generate synthesized "logs" in the frontend (e.g., `if (data.auto_assigned_deals > 0) logs.push("Auto-assigned...)`). This violates the real-world, no-mockup requirement.

**Backend Changes Required**:
1.  **Create AuditLog Model**: In the backend, define a SQLAlchemy model (`src/models/audit.py` or similar) to persistently track real actions taken by the AI or humans (e.g., `action_type`, `message`, `timestamp`).
2.  **Instrument the Engine**: Modify `src/services/living_agent.py`. Inside `_perform_autonomous_review`, when the agent successfully auto-assigns a deal or generates a nudge task, log these exact events to the database as `AuditLog` records.
3.  **New API Endpoint**: Add `GET /api/v1/crm/activity` or `GET /api/v1/crm/audit-logs` to `src/api/crm.py` which retrieves the 20 most recent real logs from the database.

**Frontend Changes Required**:
1.  **Consume Real API Data**: In `frontend/src/pages/dashboard/index.js`, update the `Activity Feed` component to fetch and map over the real array of logs returned from `GET /api/v1/crm/audit-logs`. Completely delete the logic that synthesizes strings based on stat totals.
2.  **Sentiment Heatmap**: If the current heatmap generates random opacity values (`0.6 + Math.random() * 0.4`), **remove the math.random()**. Either tie it strictly to real customer sentiment scores fetched via the API, or simplify the visualization to accurately reflect actual database averages without guessing.

## Final Review
Ensure that building and running the UI presents a completely un-broken, error-free experience. The design should feel premium, trustworthy, and perfectly polished for a real-world enterprise setting.

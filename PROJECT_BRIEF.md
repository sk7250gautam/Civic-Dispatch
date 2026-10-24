# Civic Dispatch — Project Brief
## AI-Assisted Civic Grievance, Field Operations & SLA Escalation Platform

### Executive Summary
Civic Dispatch is an enterprise-grade municipal operations and civic engagement platform designed for real-world deployment across municipal corporations, public works departments, and civic service agencies. It provides citizens with transparent grievance reporting and real-time tracking, empowers field officers with a mobile-optimized resolution workspace with GPS verification, provides department heads with actionable operations dashboards and automated SLA escalations, and gives system administrators full governance, auditability, and role-based access control.

---

### Core Goals
1. **Multi-Role End-to-End Civic Lifecycle**:
   - **Citizen**: Complaint intake (category, geo-location, address, photos, consent), tracking, status history, SLA deadline visibility, reopen capability, resolution rating.
   - **Field Officer**: Mobile-first field workspace, assigned queue, status transitions (ACKNOWLEDGE, START_WORK, RESOLVE), photo evidence upload, GPS tolerance verification, internal notes.
   - **Department Manager**: Command center, SLA compliance analytics, officer workload balancing, ticket reassignment, escalation management, CSV reporting.
   - **System Administrator**: Multi-tenant/department configuration, SLA policy rules, audit log viewer, category & service zone management, user/role management.
2. **Deterministic State Machine & Append-Only Audit**:
   - Strict transition rules (`SUBMITTED` -> `ACKNOWLEDGED` -> `ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED` -> `CLOSED` / `REOPENED` / `REJECTED`).
   - Immutable audit trail and history logs capturing timestamp, actor, transition reason, and metadata.
3. **Automated SLA Engine & Celery Escalation Queue**:
   - Dynamic SLA deadline computation per category/priority policy.
   - Celery + Redis background beat checking overdue tickets, advancing escalation tiers (Level 1 -> Level 2 -> Level 3), triggering alerts and notifications, with idempotent worker executions.
   - Local fallback CLI command for immediate SLA evaluation without waiting for workers.
4. **Geospatial & Interactive Map System**:
   - Leaflet interactive map with coordinate validation, pin placement, status/category filtering, and boundary service zones.
   - Privacy protection: Public transparency map anonymizes exact coordinates and masks sensitive categories, while officer/manager views provide operational precision.
5. **Responsible AI Assistance with Deterministic Fallbacks**:
   - Automated categorization suggestions, priority recommendations, duplicate detection (vector/token/geo-proximity), and internal summarization.
   - 100% functional local rule-based fallback without requiring external paid API keys. Clear visual labeling indicating AI-suggested vs rule-fallback status.
6. **Robust Security & Production Standards**:
   - Secure session/token auth, role-based route guards, horizontal privilege escalation prevention, file upload validation (MIME sniffing, size caps, path-traversal prevention), rate limiting, and zero credential leaks.

---

### Non-Goals
- Inventing artificial ward boundaries when official shapefiles are unavailable (system allows manual selection or honest unassigned zone).
- Making external AI services mandatory for basic operations.
- Storing unencrypted secrets or committing user uploads to version control.
- Frontend-only simulated state changes (all mutations must persist to backend database).

---

### Acceptance Criteria
- [x] Full-stack architecture: React 18 + TypeScript + Vite + Tailwind CSS frontend; Python 3.13 + Flask + SQLAlchemy + Marshmallow backend; Redis + Celery background task processing.
- [x] Database: PostgreSQL/PostGIS production support with zero-friction SQLite/PostgreSQL development switch.
- [x] Authentication & RBAC: 4 distinct roles with seed demo credentials for instant recruiter walkthrough.
- [x] Complaint workflow: 8-stage state machine with transition validations, reasons, and immutable history.
- [x] SLA Escalation Engine: Background runner + on-demand CLI command with duplicate escalation protection.
- [x] Geospatial engine: Interactive Leaflet maps with coordinate validation and privacy masking.
- [x] AI assistance: Modular NLP & rule-based categorization, duplicate detection, and summarization.
- [x] Comprehensive test suite: Unit, integration, API, security, and frontend build tests passing.
- [x] Deployment: Production-ready Docker Compose, environment configuration, and thorough setup documentation.

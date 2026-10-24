# Civic Dispatch — Master Task Matrix & Implementation Checklist

## Milestone 1: Environment & Architecture Foundations
- [ ] Task 1.1: Verify Node.js LTS and Python 3.13 runtimes
- [ ] Task 1.2: Initialize backend project structure with Python virtualenv & dependencies (`requirements.txt`)
- [ ] Task 1.3: Initialize frontend project structure with Vite, React 18, TypeScript, Tailwind CSS, Lucide icons, React Router, TanStack Query, Leaflet, Recharts

## Milestone 2: Data Models & State Machine Core
- [ ] Task 2.1: Implement database models (User, Role, Department, ServiceZone, Complaint, Attachment, StatusHistory, SLAPolicy, EscalationEvent, Notification, Feedback, AuditLog)
- [ ] Task 2.2: Implement strict state machine with transition validator and append-only history logging
- [ ] Task 2.3: Implement database seeder with realistic municipal departments, SLA policies, and role-based demo accounts

## Milestone 3: Background SLA & Escalation Engine
- [ ] Task 3.1: Implement SLA deadline calculation logic (elapsed hours, priority offsets)
- [ ] Task 3.2: Implement Celery tasks for background periodic SLA evaluation and escalation escalation levels
- [ ] Task 3.3: Implement CLI command (`python -m app.cli sla-check`) for immediate synchronous verification without Celery daemon

## Milestone 4: AI & Machine Intelligence Service Layer
- [ ] Task 4.1: Implement modular AI categorizer and priority engine with 100% deterministic local rule fallback
- [ ] Task 4.2: Implement duplicate grievance detector (fuzzy text similarity + spatial Haversine radius)
- [ ] Task 4.3: Implement grievance summarizer with PII redaction protection

## Milestone 5: Security, Uploads & REST API Layer (/api/v1)
- [ ] Task 5.1: Implement authentication, password hashing, session management, and RBAC authorization decorators
- [ ] Task 5.2: Implement secure file upload handler with MIME validation, size caps, and access-controlled streaming
- [ ] Task 5.3: Implement Citizen endpoints (create complaint, list user complaints, get details, reopen, feedback)
- [ ] Task 5.4: Implement Field Officer endpoints (assigned queue, accept, start work, resolve with photo & GPS verification)
- [ ] Task 5.5: Implement Department Manager endpoints (dashboard metrics, complaint reassignment, officer performance, CSV export)
- [ ] Task 5.6: Implement System Admin endpoints (SLA policies, audit logs, category management, user administration)
- [ ] Task 5.7: Implement Public Transparency endpoints (anonymized aggregates, resolution stats, sanitized map data)

## Milestone 6: Modern Municipal Frontend Application
- [ ] Task 6.1: Build high-contrast, accessible UI system (Navy/Slate/Teal palette, cards, badges, buttons, modals, toasts)
- [ ] Task 6.2: Build Public Portal (hero, grievance tracker by reference ID, public transparency dashboard with charts & Leaflet map)
- [ ] Task 6.3: Build Citizen Portal (intuitive submission wizard with Leaflet pin picker, active complaints tracker, timeline view, rating modal)
- [ ] Task 6.4: Build Field Officer Workspace (mobile-first queue, one-tap status actions, GPS coordinate verification, photo upload)
- [ ] Task 6.5: Build Department Manager Command Center (metrics KPI cards, SLA health gauges, Recharts resolution trends, reassignment drawer, CSV export)
- [ ] Task 6.6: Build Admin Control Panel (SLA policy manager, audit trail inspector, user role manager)
- [ ] Task 6.7: Build Quick-Role Demo Switcher bar for seamless recruiter evaluation

## Milestone 7: Automated Testing, Quality Assurance & Audit
- [ ] Task 7.1: Write backend pytest test suite covering Auth, RBAC, State Transitions, SLA escalation, File security, and AI fallback
- [ ] Task 7.2: Run frontend TypeScript typecheck and production build verification (`npm run build`)
- [ ] Task 7.3: Perform 6-point CodeRabbit quality audit (logic, security, performance, errors, tests, maintainability)

## Milestone 8: DevOps & Deployment Deliverables
- [ ] Task 8.1: Create production Dockerfile for backend and multi-stage Dockerfile for frontend
- [ ] Task 8.2: Create `docker-compose.yml` with web, api, db (PostgreSQL), redis, and celery worker services
- [ ] Task 8.3: Write comprehensive `README.md` with architectural diagrams, API documentation, local setup guide, and recruiter walkthrough instructions

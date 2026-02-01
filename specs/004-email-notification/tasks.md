# Tasks: Email Notification for Incidents

**Input**: Design documents from `/specs/004-email-notification/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths below assume extension of the existing Scandom project structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the email module

- [x] T001 Create directory structure for email module in `src/email/templates/` and `config/email/`
- [x] T002 Create configuration template in `config/email/.env.example` and `config/email/config.ini`
- [x] T003 [P] Initialize email module logger and package in `src/email/__init__.py`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create database migration for notification tracking in `migrations/006_create_email_notifications.sql`
- [x] T005 [P] Implement SMTP configuration loader in `src/email/config.py`
- [x] T006 [P] Setup Jinja2 template environment for emails in `src/email/sender.py`

**Checkpoint**: Foundation ready - email sending logic and storage can now be implemented

## Phase 3: User Story 1 - Notifier le gestionnaire lors de la création d'un incident (Priority: P1) 🎯 MVP

**Goal**: Automatically send a formatted HTML email to the building manager when an incident is created via WhatsApp

**Independent Test**: Trigger an incident creation flow, verify that a Celery task is queued, an email is sent to the manager's address, and a record is created in `email_notifications` with status 'sent'.

### Implementation for User Story 1

- [x] T007 [P] [US1] Create HTML email template in `src/email/templates/incident_created.html` (must include: floor, zone, category, description, created_at, photo links)
- [x] T008 [US1] Implement core `EmailService` with smtplib and Jinja2 rendering in `src/email/sender.py`, including handling of missing manager email (skip send and log warning)
- [x] T009 [US1] Implement `send_incident_email_task` with retry logic in `src/email/tasks.py` (include CRITICAL log after final failure, skip email for incidents with status `pending`)
- [x] T010 [US1] Add database persistence for each notification attempt in `src/email/sender.py`
- [x] T011 [US1] Integrate `send_incident_email_task.delay()` call in `src/whatsapp/conversation_manager.py` after successful incident creation, retrieving manager email from `T_BUILDING.EMAIL_GESTIONNAIRE`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Consulter l'historique des notifications envoyées (Priority: P2)

**Goal**: Allow administrators to track and verify the status of email notifications for any given incident

**Independent Test**: Query the `email_notifications` table for a known incident ID and verify the status, recipient, and any error messages are correctly displayed.

### Implementation for User Story 2

- [x] T012 [P] [US2] Implement `get_notification_status` helper in `src/email/sender.py`
- [x] T013 [US2] Create a simple CLI helper to view notification history in `src/cli/view_email_history.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, cleanup, and validation

- [x] T014 [P] Update main `README.md` with email configuration instructions
- [x] T015 [P] Documentation updates in docs/
- [x] T016 [P] Code cleanup and refactoring
- [x] T017 [P] Performance optimization across all stories
- [x] T018 [P] Ensure ≥80% test coverage for email module (`src/email/*`, `src/cli/view_email_history.py`) in `tests/email/`
- [x] T019 [P] Security hardening
- [x] T020 [P] Run quickstart.md validation

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion (MVP focus)
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion
- **Polish (Final Phase)**: Depends on Phase 3 and 4 completion

### Within Each User Story

- T007 (Template) can be done in parallel with service logic
- T008 (Service) must be done before T009 (Celery Task)
- T011 (Integration) is the final step for US1

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2
2. Complete Phase 3 (US1)
3. **STOP and VALIDATE**: Test incident creation → Email delivery
4. Proceed to Phase 4 only if MVP is stable

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Ensure `SMTP_FROM_EMAIL` is validated before sending
- Use Celery `autoretry_for` for transient SMTP errors

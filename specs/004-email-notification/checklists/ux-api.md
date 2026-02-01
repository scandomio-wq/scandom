# Requirement Quality Checklist: UX & API for Email Notifications

**Purpose**: Validate the quality and completeness of requirements for the Email Notification feature.
**Created**: 2026-01-30
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001: Are the specific data fields for the incident summary (zone, floor, category, description, photos, reporter, created_at) explicitly listed as mandatory in the template requirements? [Spec §FR-003]
- [ ] CHK002: Does the spec define the exact trigger point for the email task (e.g., immediately after DB commit, or after WhatsApp confirmation)? [Spec §FR-011]
- [ ] CHK003: Is there a requirement for a 'fallback' or 'admin notification' if the building manager email is missing? [Spec §FR-009]

## Requirement Clarity

- [ ] CHK004: Is the HTML format requirement quantified with any specific styling constraints or compatibility targets (e.g., responsive design, specific email clients)? [Spec §Clarifications]
- [ ] CHK005: Is the 'summary' content structure defined (e.g., tabular format, list format, or free text)? [Spec §FR-003]
- [ ] CHK006: Is the sender address format validated (e.g., must match a specific domain)? [Spec §FR-005]

## Scenario & Edge Case Coverage

- [ ] CHK007: Is the behavior after the FINAL retry failure explicitly defined (e.g., critical log level, alert to system admin)? [Gap]
- [ ] CHK008: Does the spec define how photo URLs are displayed if the storage service is temporarily unreachable at the time of email generation? [Gap]
- [ ] CHK009: Is the behavior defined for when multiple incidents are created for the same building in a short window (e.g., email batching vs. individual emails)? [Gap]

## Non-Functional Requirements

- [ ] CHK010: Is there a maximum size limit specified for the HTML body to avoid deliverability issues? [Gap]
- [ ] CHK011: Are there measurable performance requirements for the template rendering time? [Gap]

## Notes

- This checklist focuses on the quality of the written requirements to ensure they are ready for implementation.
- Items marked as [Gap] identify areas where the current specification may be underspecified based on best practices.

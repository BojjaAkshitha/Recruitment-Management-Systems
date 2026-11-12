# Data dictionary and relational design

All people and organizations are fictional. Dates use ISO-8601 (`YYYY-MM-DD`), timestamps use `YYYY-MM-DDTHH:MM:SS`, and salary is INR lakh per annum (LPA). `Required` means non-null in the generated records. Empty strings represent optional dates/values in CSV exports. IDs are immutable and zero-padded.

## Entity field definitions

| Entity / field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| **Department.department_id** | TEXT | Yes | `DEP-NNN` | PK | Immutable |
| Department.department_name | TEXT | Yes | Department catalog | Yes | Non-empty |
| **JobRequisition.requisition_id** | TEXT | Yes | `REQ-2026-NNNNNN` | PK | Immutable |
| JobRequisition.department_id | TEXT | Yes | Department ID | No | FK to Department |
| JobRequisition.job_title, location | TEXT | Yes | Role / synthetic city | No | Non-empty |
| JobRequisition.vacancies | INTEGER | Yes | Positions | No | Greater than zero |
| JobRequisition.min_salary_lpa, max_salary_lpa | REAL | Yes | INR LPA | No | Minimum >= 0; maximum >= minimum |
| JobRequisition.status | TEXT | Yes | Approved, Closed | No | Closed requisitions cannot accept normal active applications |
| JobRequisition.created_date, approved_date, closed_date | DATE | Yes / conditional | ISO date | No | Creation <= approval <= closure; closure date optional for open roles |
| JobRequisition.requested_by, process_owner_id, approved_by | TEXT | Yes | Actor references | No | Identifies business requester, process owner and approver |
| JobRequisition.required_skill_names | TEXT | Yes | Semicolon-separated skill names | No | Each skill must exist in Skill and ScreeningRule |
| **Candidate.candidate_id** | TEXT | Yes | `CAND-NNNNNN` | PK | Immutable |
| Candidate.full_name | TEXT | Yes | Synthetic name | No | Non-empty; fictional only |
| Candidate.email | TEXT | Yes | `candidateNNNNNN@example.test` | Yes | Reserved non-deliverable test domain |
| Candidate.city, education | TEXT | Yes | Synthetic city; B.Tech/B.Sc/MCA/M.Tech/BCA | No | Non-empty / enum |
| Candidate.experience_years | REAL | Yes | Years | No | >= 0; not used as demographic proxy |
| Candidate.created_date | DATE | Yes | ISO date | No | Valid date |
| **Application.application_id** | TEXT | Yes | `APP-<requisition-id>-<candidate-id>` | PK | Duplicate exception has explicit `-DUP-001` suffix |
| Application.requisition_id, candidate_id | TEXT | Yes | Parent IDs | No | FK to JobRequisition and Candidate |
| Application.applied_date | DATE | Yes | ISO date | No | Valid date; must not precede requisition creation |
| Application.screening_score | REAL | Yes | 0–100 points | No | Derived only from weighted required-skill matches |
| Application.screening_status | TEXT | Yes | Pass, Review, Fail | No | Derived from screening score |
| Application.current_stage | TEXT | Yes | Applied, Screening, Interview Scheduled, Interview Completed, Selected, Rejected, Withdrawn | No | Must match final history event and valid lifecycle transitions |
| Application.application_status | TEXT | Yes | Active, Rejected, Withdrawn | No | Consistent with terminal stage; closed-role exception is labelled |
| Application.source | TEXT | Yes | Career Site / Exception Injection | No | Provenance of application |
| **ResumeArtifact.resume_id** | TEXT | Yes | `RES-NNNNNN` | PK | Immutable |
| ResumeArtifact.candidate_id | TEXT | Yes | Candidate ID | No | FK to Candidate |
| ResumeArtifact.file_name | TEXT | Yes | Synthetic filename | No | Metadata only; no real resume document is generated |
| ResumeArtifact.file_type | TEXT | Yes | PDF, DOCX | No | Enum |
| ResumeArtifact.file_size_kb | INTEGER | Yes | KB | No | > 0 |
| ResumeArtifact.uploaded_date | DATE | Yes | ISO date | No | Valid date |
| ResumeArtifact.source | TEXT | Yes | synthetic_metadata | No | Provenance |
| ResumeArtifact.is_latest | BOOLEAN | Yes | true/false | No | Boolean |
| **Skill.skill_id** | TEXT | Yes | `SKL-NNN` | PK | Immutable |
| Skill.skill_name | TEXT | Yes | Skill catalog | Yes | Non-empty |
| Skill.category | TEXT | Yes | technical, soft | No | Enum |
| **CandidateSkill.candidate_id, skill_id** | TEXT | Yes | Candidate / Skill IDs | Composite PK | Both are FKs; one row per candidate-skill pair |
| CandidateSkill.proficiency | TEXT | Yes | Beginner, Intermediate, Advanced | No | Enum |
| CandidateSkill.years_experience | REAL | Yes | Years | No | >= 0 |
| **ScreeningRule.rule_id** | TEXT | Yes | `RULE-<req-id>-<skill-id>` | PK | Immutable |
| ScreeningRule.requisition_id, skill_id | TEXT | Yes | Parent IDs | Composite unique | FKs; one effective rule per requisition-skill pair |
| ScreeningRule.weight | REAL | Yes | Percentage points | No | 0–100; weights total 100 per requisition |
| ScreeningRule.is_required | BOOLEAN | Yes | true/false | No | Boolean |
| ScreeningRule.effective_from | DATE | Yes | ISO date | No | Required and <= effective_to |
| ScreeningRule.effective_to | DATE | Optional | ISO date | No | Null/blank means currently effective |
| **Interviewer.interviewer_id** | TEXT | Yes | `INTR-NNNN` | PK | Immutable |
| Interviewer.interviewer_name | TEXT | Yes | Synthetic name | No | Non-empty |
| Interviewer.department_id | TEXT | Yes | Department ID | No | FK to Department |
| Interviewer.active | BOOLEAN | Yes | true/false | No | Only active interviewers can be scheduled |
| Interviewer.availability_start, availability_end | DATE | Yes | ISO date | No | Start <= end |
| Interviewer.unavailable_dates | TEXT | Optional | Semicolon-separated dates | No | No assignment on blocked dates |
| **Interview.interview_id** | TEXT | Yes | `INT-2026-NNNNNN` | PK | Immutable |
| Interview.application_id | TEXT | Yes | Application ID | No | FK to Application |
| Interview.round_name | TEXT | Yes | Technical / Technical + HR | No | Non-empty |
| Interview.scheduled_date | DATE | Yes | ISO date | No | Within each panel member's availability |
| Interview.start_time, end_time | TIME | Yes | HH:MM | No | Start < end; no overlapping panel assignments |
| Interview.status | TEXT | Yes | Scheduled, Completed, Cancelled | No | Enum |
| Interview.availability_checked | BOOLEAN | Yes | true/false | No | False only for labelled conflict scenario |
| **InterviewPanelMember.interview_id, interviewer_id** | TEXT | Yes | Interview / Interviewer IDs | Composite PK | Bridge table; two members per generated interview |
| InterviewPanelMember.panel_role | TEXT | Yes | Technical Interviewer, Panel Member | No | Non-empty |
| **Feedback.feedback_id** | TEXT | Yes | `FB-<interview-id>-<interviewer-id>` | PK | Immutable |
| Feedback.interview_id, interviewer_id | TEXT | Yes | Panel member IDs | Composite unique | Composite FK to InterviewPanelMember |
| Feedback.technical_score, problem_solving_score, communication_score | INTEGER | Yes | 1–5 points | No | Range validation |
| Feedback.overall_score | REAL | Yes | 1–5 points | No | Arithmetic mean of the three component scores |
| Feedback.recommendation | TEXT | Yes | Strong Hire, Hire, Hold, No Hire | No | Derived from overall score |
| Feedback.comments | TEXT | Optional | Synthetic text | No | No personal/sensitive content |
| Feedback.submitted_at | TIMESTAMP | Yes | ISO timestamp | No | After interview date |
| **Offer.offer_id** | TEXT | Yes | `OFF-2026-NNNNNN` | PK | Immutable |
| Offer.application_id, requisition_id, candidate_id | TEXT | Yes | Parent IDs | No | FKs; requisition and candidate must match application |
| Offer.salary_lpa | REAL | Yes | INR LPA | No | Within requisition band for approval; one labelled proposal is outside and rejected |
| Offer.currency | TEXT | Yes | INR | No | Enum |
| Offer.approval_status | TEXT | Yes | Approved, Rejected, Pending | No | Must reconcile to approval history |
| Offer.offer_status | TEXT | Yes | Pending, Accepted, Rejected, Withdrawn | No | For approved proposals, derived from panel average score |
| Offer.approved_by | TEXT | Yes | Approver ID | No | Approval actor |
| Offer.approved_at, issued_date | DATE | Conditional | ISO date | No | Rejected offer has no issue date |
| **RequisitionStatusHistory.event_id** | TEXT | Yes | `REQEVT-NNNNNN` | PK | Append-only event |
| RequisitionStatusHistory.requisition_id | TEXT | Yes | Requisition ID | No | FK to JobRequisition |
| RequisitionStatusHistory.from_status, to_status | TEXT | Optional / Yes | Draft, Pending Approval, Approved, Closed | No | Valid ordered transitions |
| RequisitionStatusHistory.event_time | TIMESTAMP | Yes | ISO timestamp | No | Chronological |
| RequisitionStatusHistory.actor, reason | TEXT | Yes | Actor ID / explanation | No | Traceability |
| **ApplicationStatusHistory.event_id** | TEXT | Yes | `EVT-NNNNNNN` | PK | Append-only event |
| ApplicationStatusHistory.application_id | TEXT | Yes | Application ID | No | FK to Application |
| ApplicationStatusHistory.from_status, to_status | TEXT | Optional / Yes | Application stages | No | Valid transition; first event has empty from_status |
| ApplicationStatusHistory.event_time | TIMESTAMP | Yes | ISO timestamp | No | Chronological |
| ApplicationStatusHistory.actor, reason | TEXT | Yes | Actor ID / explanation | No | Traceability |
| **OfferApprovalHistory.approval_event_id** | TEXT | Yes | `APR-NNNNNN` | PK | Append-only event |
| OfferApprovalHistory.offer_id | TEXT | Yes | Offer ID | No | FK to Offer |
| OfferApprovalHistory.decision | TEXT | Yes | Approved, Rejected, Pending | No | Must equal current approval state in this generated snapshot |
| OfferApprovalHistory.approver_id | TEXT | Yes | Approver ID | No | Non-empty |
| OfferApprovalHistory.decision_date | DATE | Yes | ISO date | No | Valid date |
| OfferApprovalHistory.comments | TEXT | Optional | Decision explanation | No | Audit evidence |
| **GroundTruth.record_type, record_id, issue_type** | TEXT | Yes | Entity and exception identifiers | Composite PK | Kept separate from model input features |
| GroundTruth.expected_label, expected_decision | TEXT | Yes | Documented outcome | No | Labels generated from injected exception rules |

## Relationships and cardinality

- Department 1:N JobRequisition; Department 1:N Interviewer.
- JobRequisition 1:N Application; JobRequisition 1:N ScreeningRule; JobRequisition 1:N RequisitionStatusHistory.
- Candidate 1:N Application; Candidate 1:N ResumeArtifact; Candidate N:M Skill through CandidateSkill.
- Skill 1:N CandidateSkill and Skill 1:N ScreeningRule.
- Application 1:N Interview; Application 1:N ApplicationStatusHistory; Application 1:N Offer (one offer proposal per selected application in this sample).
- Interview N:M Interviewer through InterviewPanelMember; Interview 1:N Feedback, with one feedback row per assigned panel member.
- Offer 1:N OfferApprovalHistory.

Optional relationships: requisition closure date is optional for open roles; a candidate may have zero or more resume artifacts; feedback is required from every panel member before progression but one deliberately missing record is injected; offers are optional for applications that are not selected.

## Lifecycle and derived-value rules

Requisition: Draft → Pending Approval → Approved → Closed (closure is optional). Application: Applied → Screening → Interview Scheduled → Interview Completed → Selected; Rejected and Withdrawn are terminal from Screening. Each state change is appended to ApplicationStatusHistory. Offers are created only for Selected applications when all panel members recommend Hire/Strong Hire. Offer approval is rejected if salary is outside the approved requisition band. Approved offer outcome is derived from panel average: >=4.2 Accepted, >=3.7 Pending, otherwise Rejected. Screening score is the sum of weights for required skills possessed by the candidate; it does not use demographic attributes or proxies.

## Intentional exceptions

`ground_truth.csv/json` contains exactly five injected negative scenarios: unavailable interviewer, duplicate application, missing required feedback after stage advancement, out-of-band offer proposal (approval rejected and not issued), and active application on a closed requisition. These records remain visible for audit and evaluation; they are not silently repaired.

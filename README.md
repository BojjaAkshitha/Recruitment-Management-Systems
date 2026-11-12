# Recruitment Management System — End-to-End Synthetic Workflow

A deterministic Python/SQLite implementation of the recruitment workflow in the assignment: requisitions, candidate profiles, resumes, job-related screening, applications, interview panels, structured feedback, offers, approvals, audit history, labelled exceptions and measurable validation outputs.

## Requirements
- Python 3.10 or newer (tested with Python 3.11).
- Core generator uses only the Python standard library.
- `pytest` is used for automated tests.

## Run on Windows PowerShell
Run commands from the folder containing `requirements.txt`:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 -m src.generate
py -3.11 -m src.validation
py -3.11 -m pytest -q
py -3.11 -m src.reproducibility
```

Expected checks: structural validation errors `[]`; five labelled business exceptions; all tests pass; reproducibility prints `REPRODUCIBLE: True`.

## Default scale and configuration
The default seed is `20261022`. Baseline volumes are 100 requisitions, 2,000 candidates, 3,000 applications, 600 interviews and 150 offers. `src/config.py` parameterizes scale and output directory. Two additional application rows are intentionally injected to represent duplicate application and active application on a closed role; therefore operational application output has 3,002 rows while the baseline remains 3,000.

## Workflow and business rules
1. Generate departments, skills, approved/closed requisitions, candidates, candidate-skill links, resume metadata, interviewers and effective-dated screening rules before transactions.
2. Create 3,000 unique baseline applications only against approved requisitions.
3. Compute screening scores from weighted matches against each requisition's required skills. No demographic attributes or demographic proxies are used.
4. Schedule 600 interviews only when two active interviewers are available for the date and time slot. Each interview has a two-person panel and individual feedback records.
5. Progress applications through a documented lifecycle. Append-only status events record each transition and reconcile to the current stage.
6. Select candidates only when both panel members submit `Hire` or `Strong Hire` feedback. Create 150 offer proposals and record the approval decision. Offer acceptance outcome is derived from the mean panel score (>=4.2 Accepted, 3.7–4.19 Pending, below 3.7 Rejected), not independently randomized.
7. Record requisition approval/closure events and offer approval history for traceability.
8. Inject five deliberate, separately labelled anomalies after the valid baseline has been generated.

## Five deliberate exceptions
- One interview panel assignment on an unavailable interviewer date.
- One duplicate candidate/requisition application (explicit `-DUP-001` audit suffix).
- One application advanced to Interview Completed while one panel member's feedback is missing.
- One offer proposal outside the approved salary band; its approval is Rejected and it is not issued.
- One active application linked to a closed requisition.

`data/ground_truth.csv` and `.json` contain the known issue labels and expected decisions. Do not use ground-truth labels as model input features.

## Outputs
- CSV and JSON for every table in `data/`.
- `data/recruitment.db`: queryable SQLite export.
- `data/seed_data.sql`: standalone SQL DDL and INSERT export.
- `data/validation_summary.json`: requested/actual counts, screening and stage distributions, interview feedback completion, offer approval/outcome metrics, structural validation results, business exception findings and SHA-256 checksums.
- `data/source_manifest.json`: seed, provenance and output row counts.
- `database/schema.sql`: relational schema with primary keys, foreign keys, bridge tables and constraints.
- `docs/data_dictionary.md`: field-level dictionary, relationships, cardinalities and lifecycle notes.

## Entity relationships
- Department 1:N JobRequisition and Interviewer.
- JobRequisition 1:N Application and ScreeningRule.
- Candidate 1:N Application and ResumeArtifact.
- Candidate N:M Skill through CandidateSkill.
- Skill 1:N ScreeningRule.
- Application 1:N Interview and ApplicationStatusHistory.
- Interview N:M Interviewer through InterviewPanelMember.
- Interview 1:N Feedback (one feedback per panel member).
- Application 1:N Offer (the sample produces one proposal per selected application).
- Offer 1:N OfferApprovalHistory.
- JobRequisition 1:N RequisitionStatusHistory.

## Validation and interpretation
`src.generator.validate()` checks primary/foreign keys, composite keys, enum/range checks, dates, screening arithmetic, panel membership, status transitions, event-history reconciliation and offer-approval reconciliation. `src.validation.run_business_validation()` separately detects the five intentional policy exceptions. Those findings are expected negative scenarios, not unexplained generator failures.

The dataset is synthetic and contains no real candidate identities or resume files; resume artifacts are metadata only. This is a workflow/data-generation demonstration, not a production ATS or an automated hiring decision tool.

## Public GitHub submission
Create a public repository named `Recruitment-Management-System`, then from this project folder:

```powershell
git init
git add .
git commit -m "Build end-to-end recruitment synthetic workflow"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Recruitment-Management-System.git
git push -u origin main
```
Replace `YOUR_USERNAME` with your GitHub username. Confirm repository visibility is Public.

PRAGMA foreign_keys = ON;

CREATE TABLE departments (
  department_id TEXT PRIMARY KEY,
  department_name TEXT NOT NULL UNIQUE
);
CREATE TABLE skills (
  skill_id TEXT PRIMARY KEY,
  skill_name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL CHECK(category IN ('technical','soft'))
);
CREATE TABLE job_requisitions (
  requisition_id TEXT PRIMARY KEY,
  department_id TEXT NOT NULL REFERENCES departments(department_id),
  job_title TEXT NOT NULL,
  location TEXT NOT NULL,
  vacancies INTEGER NOT NULL CHECK(vacancies > 0),
  min_salary_lpa REAL NOT NULL CHECK(min_salary_lpa >= 0),
  max_salary_lpa REAL NOT NULL CHECK(max_salary_lpa >= min_salary_lpa),
  status TEXT NOT NULL CHECK(status IN ('Approved','Closed')),
  created_date TEXT NOT NULL,
  approved_date TEXT,
  closed_date TEXT,
  requested_by TEXT NOT NULL,
  process_owner_id TEXT NOT NULL,
  approved_by TEXT NOT NULL,
  required_skill_names TEXT NOT NULL
);
CREATE TABLE requisition_status_history (
  event_id TEXT PRIMARY KEY,
  requisition_id TEXT NOT NULL REFERENCES job_requisitions(requisition_id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  event_time TEXT NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL
);
CREATE TABLE candidates (
  candidate_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  city TEXT NOT NULL,
  education TEXT NOT NULL,
  experience_years REAL NOT NULL CHECK(experience_years >= 0),
  created_date TEXT NOT NULL
);
CREATE TABLE candidate_skills (
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  skill_id TEXT NOT NULL REFERENCES skills(skill_id),
  proficiency TEXT NOT NULL CHECK(proficiency IN ('Beginner','Intermediate','Advanced')),
  years_experience REAL NOT NULL CHECK(years_experience >= 0),
  PRIMARY KEY(candidate_id, skill_id)
);
CREATE TABLE resume_artifacts (
  resume_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL CHECK(file_type IN ('PDF','DOCX')),
  file_size_kb INTEGER NOT NULL CHECK(file_size_kb > 0),
  uploaded_date TEXT NOT NULL,
  source TEXT NOT NULL,
  is_latest INTEGER NOT NULL CHECK(is_latest IN (0,1))
);
CREATE TABLE screening_rules (
  rule_id TEXT PRIMARY KEY,
  requisition_id TEXT NOT NULL REFERENCES job_requisitions(requisition_id),
  skill_id TEXT NOT NULL REFERENCES skills(skill_id),
  weight REAL NOT NULL CHECK(weight >= 0 AND weight <= 100),
  is_required INTEGER NOT NULL CHECK(is_required IN (0,1)),
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  UNIQUE(requisition_id, skill_id)
);
CREATE TABLE interviewers (
  interviewer_id TEXT PRIMARY KEY,
  interviewer_name TEXT NOT NULL,
  department_id TEXT NOT NULL REFERENCES departments(department_id),
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  availability_start TEXT NOT NULL,
  availability_end TEXT NOT NULL,
  unavailable_dates TEXT
);
CREATE TABLE applications (
  application_id TEXT PRIMARY KEY,
  requisition_id TEXT NOT NULL REFERENCES job_requisitions(requisition_id),
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  applied_date TEXT NOT NULL,
  screening_score REAL NOT NULL CHECK(screening_score BETWEEN 0 AND 100),
  screening_status TEXT NOT NULL CHECK(screening_status IN ('Pass','Fail','Review')),
  current_stage TEXT NOT NULL CHECK(current_stage IN ('Applied','Screening','Interview Scheduled','Interview Completed','Selected','Rejected','Withdrawn')),
  application_status TEXT NOT NULL CHECK(application_status IN ('Active','Rejected','Withdrawn')),
  source TEXT NOT NULL
);
CREATE TABLE interviews (
  interview_id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL REFERENCES applications(application_id),
  round_name TEXT NOT NULL,
  scheduled_date TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Scheduled','Completed','Cancelled')),
  availability_checked INTEGER NOT NULL CHECK(availability_checked IN (0,1)),
  CHECK(start_time < end_time)
);
CREATE TABLE interview_panel_members (
  interview_id TEXT NOT NULL REFERENCES interviews(interview_id),
  interviewer_id TEXT NOT NULL REFERENCES interviewers(interviewer_id),
  panel_role TEXT NOT NULL,
  PRIMARY KEY(interview_id, interviewer_id)
);
CREATE TABLE feedback (
  feedback_id TEXT PRIMARY KEY,
  interview_id TEXT NOT NULL REFERENCES interviews(interview_id),
  interviewer_id TEXT NOT NULL REFERENCES interviewers(interviewer_id),
  technical_score INTEGER NOT NULL CHECK(technical_score BETWEEN 1 AND 5),
  problem_solving_score INTEGER NOT NULL CHECK(problem_solving_score BETWEEN 1 AND 5),
  communication_score INTEGER NOT NULL CHECK(communication_score BETWEEN 1 AND 5),
  overall_score REAL NOT NULL CHECK(overall_score BETWEEN 1 AND 5),
  recommendation TEXT NOT NULL CHECK(recommendation IN ('Strong Hire','Hire','Hold','No Hire')),
  comments TEXT,
  submitted_at TEXT NOT NULL,
  UNIQUE(interview_id, interviewer_id),
  FOREIGN KEY(interview_id, interviewer_id) REFERENCES interview_panel_members(interview_id, interviewer_id)
);
CREATE TABLE application_status_history (
  event_id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL REFERENCES applications(application_id),
  from_status TEXT,
  to_status TEXT NOT NULL,
  event_time TEXT NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL
);
CREATE TABLE offers (
  offer_id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL REFERENCES applications(application_id),
  requisition_id TEXT NOT NULL REFERENCES job_requisitions(requisition_id),
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  salary_lpa REAL NOT NULL CHECK(salary_lpa >= 0),
  currency TEXT NOT NULL CHECK(currency = 'INR'),
  approval_status TEXT NOT NULL CHECK(approval_status IN ('Pending','Approved','Rejected')),
  offer_status TEXT NOT NULL CHECK(offer_status IN ('Pending','Accepted','Rejected','Withdrawn')),
  approved_by TEXT NOT NULL,
  approved_at TEXT,
  issued_date TEXT,
  CHECK(approval_status != 'Rejected' OR issued_date IS NULL)
);
CREATE TABLE offer_approval_history (
  approval_event_id TEXT PRIMARY KEY,
  offer_id TEXT NOT NULL REFERENCES offers(offer_id),
  decision TEXT NOT NULL CHECK(decision IN ('Approved','Rejected','Pending')),
  approver_id TEXT NOT NULL,
  decision_date TEXT NOT NULL,
  comments TEXT
);
CREATE TABLE ground_truth (
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  expected_label TEXT NOT NULL,
  expected_decision TEXT NOT NULL,
  PRIMARY KEY(record_type, record_id, issue_type)
);

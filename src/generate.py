import json
from collections import Counter
from pathlib import Path
from .config import Config
from .generator import generate, validate, export, write_sqlite, write_sql_seed, checksums
from .validation import run_business_validation

def build_metrics(t):
    stages=Counter(x["current_stage"] for x in t["applications"])
    screening=Counter(x["screening_status"] for x in t["applications"] if x["source"]!="Exception Injection")
    offer_status=Counter(x["offer_status"] for x in t["offers"])
    approval=Counter(x["approval_status"] for x in t["offers"])
    req_status=Counter(x["status"] for x in t["job_requisitions"])
    panel_slots=len(t["interview_panel_members"])
    feedback_completion=len(t["feedback"])/panel_slots if panel_slots else 0
    baseline_apps=[x for x in t["applications"] if x["source"]!="Exception Injection" and "-DUP-" not in x["application_id"]]
    return {
        "requisition_status_counts":dict(sorted(req_status.items())),
        "application_stage_counts":dict(sorted(stages.items())),
        "screening_outcome_counts":dict(sorted(screening.items())),
        "average_screening_score":round(sum(x["screening_score"] for x in baseline_apps)/len(baseline_apps),2) if baseline_apps else 0,
        "interviews_completed":sum(1 for x in t["interviews"] if x["status"]=="Completed"),
        "panel_member_assignments":panel_slots,
        "feedback_completion_rate":round(feedback_completion,4),
        "offer_approval_counts":dict(sorted(approval.items())),
        "offer_outcome_counts":dict(sorted(offer_status.items())),
        "labelled_exception_count":len(t["ground_truth"])
    }

def main():
    cfg=Config(); tables=generate(cfg); structural=validate(tables); business=run_business_validation(tables)
    export(tables,cfg.output_dir); write_sqlite(tables,Path(cfg.output_dir)/"recruitment.db"); write_sql_seed(tables,Path(cfg.output_dir)/"seed_data.sql")
    summary={"seed":cfg.seed,"requested_counts":{"job_requisitions":cfg.requisitions,"candidates":cfg.candidates,"applications":cfg.applications,"interviews":cfg.interviews,"offers":cfg.offers},"actual_counts":{k:len(v) for k,v in tables.items()},"metrics":build_metrics(tables),"structural_validation_errors":structural,"business_exception_findings":business,"ground_truth_issue_count":len(tables["ground_truth"]),"checksums":checksums(cfg.output_dir)}
    Path(cfg.output_dir,"validation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="checksums"},indent=2))
    if structural: raise SystemExit("Structural validation failed")
    if cfg.inject_anomalies and len(tables["ground_truth"])!=5: raise SystemExit("Expected exactly five labelled anomalies")
if __name__=="__main__": main()

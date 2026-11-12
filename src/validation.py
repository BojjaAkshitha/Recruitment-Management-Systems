"""Business-policy exception detection. Expected exceptions are documented in ground_truth."""
from collections import Counter, defaultdict
from .config import Config
from .generator import generate


def run_business_validation(t):
    findings=[]
    req={r["requisition_id"]:r for r in t["job_requisitions"]}
    interviewers={r["interviewer_id"]:r for r in t["interviewers"]}
    apps=t["applications"]
    pairs=defaultdict(list)
    for a in apps: pairs[(a["requisition_id"],a["candidate_id"])].append(a["application_id"])
    for pair,ids in pairs.items():
        if len(ids)>1: findings.append({"rule":"DUPLICATE_APPLICATION","key":str(pair),"record_ids":sorted(ids)})
    panel_by_interview=defaultdict(list)
    for p in t["interview_panel_members"]: panel_by_interview[p["interview_id"]].append(p)
    for it in t["interviews"]:
        for p in panel_by_interview[it["interview_id"]]:
            interviewer=interviewers[p["interviewer_id"]]
            blocked=interviewer["unavailable_dates"].split(";") if interviewer["unavailable_dates"] else []
            if it["scheduled_date"] in blocked or not (interviewer["availability_start"]<=it["scheduled_date"]<=interviewer["availability_end"]):
                findings.append({"rule":"INTERVIEWER_UNAVAILABLE","key":it["interview_id"],"interviewer_id":p["interviewer_id"]})
    feedback_keys={(f["interview_id"],f["interviewer_id"]) for f in t["feedback"]}
    for a in apps:
        if a["current_stage"] in {"Interview Completed","Selected"}:
            its=[it for it in t["interviews"] if it["application_id"]==a["application_id"]]
            for it in its:
                for p in panel_by_interview[it["interview_id"]]:
                    if (it["interview_id"],p["interviewer_id"]) not in feedback_keys:
                        findings.append({"rule":"MISSING_REQUIRED_FEEDBACK","key":a["application_id"],"interview_id":it["interview_id"],"interviewer_id":p["interviewer_id"]})
    for o in t["offers"]:
        r=req[o["requisition_id"]]
        if not r["min_salary_lpa"]<=o["salary_lpa"]<=r["max_salary_lpa"]:
            findings.append({"rule":"OFFER_OUTSIDE_SALARY_BAND","key":o["offer_id"],"approval_status":o["approval_status"]})
    for a in apps:
        if req[a["requisition_id"]]["status"]=="Closed" and a["application_status"]=="Active":
            findings.append({"rule":"CLOSED_REQUISITION_ACTIVE_APPLICATION","key":a["application_id"]})
    return findings

if __name__=="__main__":
    data=generate(Config())
    for row in run_business_validation(data): print(row)

"""Deterministic end-to-end synthetic recruitment workflow generator.

All profiles and organizations are fictional. No external personal data is used.
Run: py -3.11 -m src.generate
"""
from __future__ import annotations
import csv, json, random, hashlib, sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import Counter, defaultdict
from .config import Config

FIRST = ["Aarav","Aditi","Ananya","Arjun","Diya","Ishaan","Kavya","Meera","Neha","Rahul","Riya","Saanvi","Vihaan","Ira","Dev","Mira","Kiran","Nikhil","Priya","Varun"]
LAST = ["Sharma","Reddy","Patel","Rao","Iyer","Kumar","Mehta","Nair","Das","Kapoor","Joshi","Singh","Menon","Gupta","Verma","Bose","Pillai","Naidu","Mishra","Shah"]
CITIES = ["Hyderabad","Bengaluru","Chennai","Pune","Mumbai","Delhi","Kochi","Jaipur"]
DEPARTMENTS = ["Engineering","Data Science","Product","Quality Assurance","IT Operations","Finance","Human Resources"]
ROLES = ["Python Developer","Data Analyst","ML Engineer","QA Engineer","Backend Developer","Frontend Developer","DevOps Engineer","IT Support Associate","Data Engineer","Business Analyst"]
SKILLS = ["Python","SQL","Problem Solving","Machine Learning","Pandas","NumPy","Java","JavaScript","HTML","CSS","REST APIs","Git","Linux","Docker","Communication","Statistics","Excel","Cloud Fundamentals","Testing","Data Visualization"]


def _csv(path, rows):
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def _json(path, rows):
    path.write_text(json.dumps(list(rows), indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def generate(config: Config):
    rng = random.Random(config.seed)
    # 1. Master/reference entities
    departments = [{"department_id": f"DEP-{i+1:03d}", "department_name": n} for i,n in enumerate(DEPARTMENTS)]
    skills = [{"skill_id": f"SKL-{i+1:03d}", "skill_name": s, "category": "soft" if s == "Communication" else "technical"} for i,s in enumerate(SKILLS)]
    skill_id = {x["skill_name"]: x["skill_id"] for x in skills}
    candidates, candidate_skills, candidate_skill_map = [], [], {}
    for i in range(1, config.candidates+1):
        cid = f"CAND-{i:06d}"
        candidates.append({"candidate_id":cid,"full_name":f"{rng.choice(FIRST)} {rng.choice(LAST)}","email":f"candidate{i:06d}@example.test","city":rng.choice(CITIES),"education":rng.choice(["B.Tech","B.Sc","MCA","M.Tech","BCA"]),"experience_years":rng.choice([0,0,0,1,2,3,4]),"created_date":"2026-01-01"})
        chosen = set(rng.sample(SKILLS, k=rng.randint(2,8)))
        candidate_skill_map[cid] = chosen
        for s in sorted(chosen):
            candidate_skills.append({"candidate_id":cid,"skill_id":skill_id[s],"proficiency":rng.choice(["Beginner","Intermediate","Advanced"]),"years_experience":round(rng.uniform(0,4),1)})

    requisitions = []
    for i in range(1, config.requisitions+1):
        status = "Approved" if i <= int(config.requisitions*0.85) else "Closed"
        low = rng.choice([3.0,3.5,4.0,4.5,5.0]); high = low + rng.choice([2.0,2.5,3.0])
        required = rng.sample(SKILLS[:16], k=3)
        requisitions.append({"requisition_id":f"REQ-2026-{i:06d}","department_id":departments[(i-1)%len(departments)]["department_id"],"job_title":ROLES[(i-1)%len(ROLES)],"location":rng.choice(CITIES),"vacancies":rng.randint(1,8),"min_salary_lpa":low,"max_salary_lpa":high,"status":status,"created_date":"2026-01-01","approved_date":"2026-01-03","closed_date":"2026-10-01" if status=="Closed" else "","requested_by":"BUSINESS-REQUESTER-001","process_owner_id":"PROCESS-OWNER-001","approved_by":"APPROVER-001","required_skill_names":";".join(required)})
    approved_reqs = [r for r in requisitions if r["status"] == "Approved"]
    closed_reqs = [r for r in requisitions if r["status"] == "Closed"]

    resume_artifacts = [{"resume_id":f"RES-{i:06d}","candidate_id":c["candidate_id"],"file_name":f"{c['candidate_id']}_resume.pdf","file_type":"PDF","file_size_kb":rng.randint(80,900),"uploaded_date":"2026-01-02","source":"synthetic_metadata","is_latest":True} for i,c in enumerate(candidates,1)]

    # Interviewers and availability. Unavailability is explicit and date-based.
    interviewers=[]
    for i in range(1,31):
        unavailable = "2026-11-10;2026-11-20" if i % 7 == 0 else ""
        interviewers.append({"interviewer_id":f"INTR-{i:04d}","interviewer_name":f"{rng.choice(FIRST)} {rng.choice(LAST)}","department_id":departments[(i-1)%len(departments)]["department_id"],"active":True,"availability_start":"2026-11-01","availability_end":"2026-11-30","unavailable_dates":unavailable})

    # Requisition/skill bridge represented by effective-dated screening rules.
    screening_rules=[]
    for req in requisitions:
        names=req["required_skill_names"].split(";")
        weights=[34.0,33.0,33.0]
        for name,weight in zip(names,weights):
            screening_rules.append({"rule_id":f"RULE-{req['requisition_id']}-{skill_id[name]}","requisition_id":req["requisition_id"],"skill_id":skill_id[name],"weight":weight,"is_required":True,"effective_from":"2026-01-01","effective_to":""})

    # 2. Generate 3,000 unique baseline applications against approved requisitions only.
    possible=[(r,c) for r in approved_reqs for c in candidates]
    rng.shuffle(possible)
    if config.applications > len(possible): raise ValueError("Requested application count exceeds unique requisition/candidate pairs")
    applications=[]; app_score={}; app_req={}
    for idx,(req,cand) in enumerate(possible[:config.applications],1):
        aid=f"APP-{req['requisition_id']}-{cand['candidate_id']}"
        reqskills=req["required_skill_names"].split(";")
        matched=sum(1 for s in reqskills if s in candidate_skill_map[cand["candidate_id"]])
        score=round(sum(w for s,w in zip(reqskills,[34.0,33.0,33.0]) if s in candidate_skill_map[cand["candidate_id"]]),2)
        applications.append({"application_id":aid,"requisition_id":req["requisition_id"],"candidate_id":cand["candidate_id"],"applied_date":"2026-02-01","screening_score":score,"screening_status":"Pass" if score>=50 else ("Review" if score>=34 else "Fail"),"current_stage":"Applied","application_status":"Active","source":"Career Site"})
        app_score[aid]=score; app_req[aid]=req

    # 3. Create a deterministic, valid interview cohort: only job-related screening passes.
    eligible=sorted([a for a in applications if a["screening_score"]>=34],key=lambda a:(-a["screening_score"],a["application_id"]))
    if len(eligible)<config.interviews: raise ValueError("Not enough screening-eligible applications to satisfy interview volume")
    interview_apps=eligible[:config.interviews]
    interviewers_by_id={x["interviewer_id"]:x for x in interviewers}
    blocked=set(); panel_members=[]; interviews=[]; feedback=[]
    dates=[date(2026,11,1)+timedelta(days=i) for i in range(30)]
    slots=[("09:00","10:00"),("11:00","12:00"),("14:00","15:00")]
    for n,app in enumerate(interview_apps,1):
        chosen=None
        for day in dates:
            ds=day.isoformat()
            for start,end in slots:
                available=[]
                for interviewer in interviewers:
                    iid=interviewer["interviewer_id"]
                    unavailable=interviewer["unavailable_dates"].split(";") if interviewer["unavailable_dates"] else []
                    if interviewer["availability_start"]<=ds<=interviewer["availability_end"] and ds not in unavailable and (iid,ds,start) not in blocked:
                        available.append(iid)
                    if len(available)==2: break
                if len(available)==2:
                    chosen=(ds,start,end,available); break
            if chosen: break
        if not chosen: raise RuntimeError("Could not find an available two-person interview panel")
        ds,start,end,panel=chosen
        for iid in panel: blocked.add((iid,ds,start))
        iid=f"INT-2026-{n:06d}"
        interviews.append({"interview_id":iid,"application_id":app["application_id"],"round_name":"Technical" if n%2 else "Technical + HR","scheduled_date":ds,"start_time":start,"end_time":end,"status":"Completed","availability_checked":True})
        for interviewer_id in panel:
            panel_members.append({"interview_id":iid,"interviewer_id":interviewer_id,"panel_role":"Technical Interviewer" if panel.index(interviewer_id)==0 else "Panel Member"})
            tech=rng.randint(2,5); problem=rng.randint(2,5); comm=rng.randint(2,5)
            overall=round((tech+problem+comm)/3,2)
            rec="Strong Hire" if overall>=4.3 else "Hire" if overall>=3.3 else "Hold" if overall>=2.7 else "No Hire"
            feedback.append({"feedback_id":f"FB-{iid}-{interviewer_id}","interview_id":iid,"interviewer_id":interviewer_id,"technical_score":tech,"problem_solving_score":problem,"communication_score":comm,"overall_score":overall,"recommendation":rec,"comments":"Synthetic structured feedback","submitted_at":ds+"T16:00:00"})

    # Pick 150 offers only from candidates whose two panel members recommend Hire/Strong Hire.
    fb_by_interview=defaultdict(list)
    for f in feedback: fb_by_interview[f["interview_id"]].append(f)
    interview_by_app={x["application_id"]:x for x in interviews}
    offer_eligible=[]
    for app in interview_apps:
        it=interview_by_app[app["application_id"]]
        fbs=fb_by_interview[it["interview_id"]]
        if len(fbs)==2 and all(f["recommendation"] in ("Hire","Strong Hire") for f in fbs):
            offer_eligible.append((app,it,sum(f["overall_score"] for f in fbs)/2))
    offer_eligible.sort(key=lambda x:(-x[2],-x[0]["screening_score"],x[0]["application_id"]))
    if len(offer_eligible)<config.offers: raise RuntimeError(f"Only {len(offer_eligible)} interview outcomes qualify for {config.offers} offers; adjust seed/scale")
    selected_ids={x[0]["application_id"] for x in offer_eligible[:config.offers]}
    interview_app_ids={a["application_id"] for a in interview_apps}

    # Derive current stage and full append-only history for each baseline application.
    history=[]
    def add_event(aid, old, new, day, reason):
        history.append({"event_id":f"EVT-{len(history)+1:07d}","application_id":aid,"from_status":old,"to_status":new,"event_time":day,"actor":"SYSTEM","reason":reason})
    for app in applications:
        aid=app["application_id"]
        transitions=[("Applied","2026-02-01T09:00:00","Application submitted")]
        if aid in interview_app_ids:
            transitions += [("Screening","2026-02-02T09:00:00","Job-related skills screening completed"),("Interview Scheduled","2026-10-25T09:00:00","Screening threshold met; interview scheduled"),("Interview Completed","2026-11-30T17:00:00","Interview panel completed feedback")]
            if aid in selected_ids: transitions.append(("Selected","2026-12-01T10:00:00","Required panel feedback supports selection"))
        else:
            # Deterministic distribution across non-interview lifecycle states.
            bucket=int(hashlib.sha256(aid.encode()).hexdigest()[:8],16)%4
            if bucket==0: transitions.append(("Screening","2026-02-02T09:00:00","Application entered screening"))
            elif bucket==1: transitions += [("Screening","2026-02-02T09:00:00","Application entered screening"),("Rejected","2026-02-03T09:00:00","Did not meet job-related screening threshold")]
            elif bucket==2: transitions += [("Screening","2026-02-02T09:00:00","Application entered screening"),("Withdrawn","2026-02-03T09:00:00","Candidate withdrew application")]
        for j,(stage,when,reason) in enumerate(transitions):
            old=transitions[j-1][0] if j else ""
            add_event(aid,old,stage,when,reason)
        app["current_stage"]=transitions[-1][0]
        app["application_status"]="Rejected" if app["current_stage"]=="Rejected" else "Withdrawn" if app["current_stage"]=="Withdrawn" else "Active"

    # 4. Offers: 150 proposals for selected applications; one deliberately rejected out-of-band.
    offers=[]; approval_history=[]
    selected_apps=[a for a in applications if a["application_id"] in selected_ids]
    for n,app in enumerate(sorted(selected_apps,key=lambda x:x["application_id"]),1):
        req=app_req[app["application_id"]]
        salary=round(rng.uniform(req["min_salary_lpa"],req["max_salary_lpa"]),2)
        approval="Approved"; decision="Approved"; comments="Approved within requisition salary band"
        if config.inject_anomalies and n==1:
            salary=round(req["max_salary_lpa"]+2.0,2); approval="Rejected"; decision="Rejected"; comments="Rejected: proposed salary exceeds approved requisition band"
        offer_outcome=("Accepted" if sum(f["overall_score"] for f in fb_by_interview[interview_by_app[app["application_id"]]["interview_id"]])/2>=4.2 else "Rejected" if sum(f["overall_score"] for f in fb_by_interview[interview_by_app[app["application_id"]]["interview_id"]])/2<3.7 else "Pending") if approval=="Approved" else "Rejected"
        offer={"offer_id":f"OFF-2026-{n:06d}","application_id":app["application_id"],"requisition_id":req["requisition_id"],"candidate_id":app["candidate_id"],"salary_lpa":salary,"currency":"INR","approval_status":approval,"offer_status":offer_outcome,"approved_by":"APPROVER-001","approved_at":"2026-12-02","issued_date":"2026-12-03" if approval=="Approved" else None}
        offers.append(offer)
        approval_history.append({"approval_event_id":f"APR-{n:06d}","offer_id":offer["offer_id"],"decision":decision,"approver_id":"APPROVER-001","decision_date":"2026-12-02","comments":comments})

    # 5. Five labelled exceptions, injected after clean baseline creation.
    ground_truth=[]
    if config.inject_anomalies:
        # Interviewer unavailable: one panel member assigned to their unavailable date.
        target=interviews[0]
        unavailable=next(x for x in interviewers if x["unavailable_dates"])
        blocked_day=unavailable["unavailable_dates"].split(";")[0]
        target["scheduled_date"]=blocked_day; target["availability_checked"]=False
        panel_row=next(x for x in panel_members if x["interview_id"]==target["interview_id"])
        panel_row["interviewer_id"]=unavailable["interviewer_id"]
        # Keep feedback relationship aligned with the deliberately unavailable panelist.
        for f in feedback:
            if f["interview_id"]==target["interview_id"]:
                if f["interviewer_id"]==next((x["interviewer_id"] for x in panel_members if x["interview_id"]==target["interview_id"] and x["interviewer_id"]!=panel_row["interviewer_id"]),""):
                    f["submitted_at"]=blocked_day+"T16:00:00"
                else:
                    f["interviewer_id"]=panel_row["interviewer_id"]; f["feedback_id"]=f"FB-{target['interview_id']}-{panel_row['interviewer_id']}"; f["submitted_at"]=blocked_day+"T16:00:00"
        ground_truth.append({"record_type":"InterviewPanelMember","record_id":target["interview_id"],"issue_type":"INTERVIEWER_UNAVAILABLE","expected_label":"CONFLICT","expected_decision":"Flag interview and reschedule with an available panelist"})

        # Duplicate application: same candidate/requisition pair, explicit audit suffix.
        src=applications[0]; dup=dict(src); dup["application_id"]=src["application_id"]+"-DUP-001"; dup["current_stage"]="Applied"; dup["application_status"]="Active"
        applications.append(dup); add_event(dup["application_id"],"","Applied","2026-02-01T09:00:00","Deliberate duplicate application exception")
        ground_truth.append({"record_type":"Application","record_id":dup["application_id"],"issue_type":"DUPLICATE_APPLICATION","expected_label":"DUPLICATE","expected_decision":"Flag duplicate and retain for audit; do not progress twice"})

        # Missing one panel member's feedback while the application is already advanced.
        target2=next(x for x in interviews if x["application_id"] not in selected_ids)
        missing_member=next(x for x in panel_members if x["interview_id"]==target2["interview_id"])
        feedback=[f for f in feedback if not (f["interview_id"]==target2["interview_id"] and f["interviewer_id"]==missing_member["interviewer_id"])]
        ground_truth.append({"record_type":"Application","record_id":target2["application_id"],"issue_type":"MISSING_FEEDBACK_STAGE_ADVANCED","expected_label":"MISSING_REQUIRED_FEEDBACK","expected_decision":"Flag and block further progression until all panel feedback is submitted"})

        # Out-of-band offer already has a rejected approval decision (never approved/issued).
        ground_truth.append({"record_type":"Offer","record_id":offers[0]["offer_id"],"issue_type":"OFFER_OUTSIDE_SALARY_BAND","expected_label":"OUT_OF_BAND","expected_decision":"Reject approval; do not issue offer outside approved band"})

        # Active application on closed requisition, with explicit exception history.
        req=closed_reqs[0]; cand=candidates[-1]; aid=f"APP-{req['requisition_id']}-{cand['candidate_id']}-EXC-001"
        applications.append({"application_id":aid,"requisition_id":req["requisition_id"],"candidate_id":cand["candidate_id"],"applied_date":"2026-10-10","screening_score":0.0,"screening_status":"Fail","current_stage":"Applied","application_status":"Active","source":"Exception Injection"})
        add_event(aid,"","Applied","2026-10-10T09:00:00","Application on closed requisition exception")
        ground_truth.append({"record_type":"Application","record_id":aid,"issue_type":"CLOSED_REQUISITION_ACTIVE_APPLICATION","expected_label":"INVALID_ACTIVE_APPLICATION","expected_decision":"Flag and close or transfer according to requisition policy"})

    requisition_history=[]
    for req in requisitions:
        chain=[("Draft","2026-01-01T09:00:00","Business requester created requisition"),("Pending Approval","2026-01-02T09:00:00","Submitted to process owner"),("Approved","2026-01-03T09:00:00","Approved by authorized approver")]
        if req["status"]=="Closed": chain.append(("Closed","2026-10-01T17:00:00","Requisition closed by process owner"))
        for j,(stage,when,reason) in enumerate(chain):
            requisition_history.append({"event_id":f"REQEVT-{len(requisition_history)+1:06d}","requisition_id":req["requisition_id"],"from_status":chain[j-1][0] if j else "","to_status":stage,"event_time":when,"actor":"BUSINESS-REQUESTER-001" if j==0 else "APPROVER-001" if j==2 else "PROCESS-OWNER-001","reason":reason})

    tables={"departments":departments,"job_requisitions":requisitions,"requisition_status_history":requisition_history,"candidates":candidates,"skills":skills,"candidate_skills":candidate_skills,"resume_artifacts":resume_artifacts,"screening_rules":screening_rules,"interviewers":interviewers,"applications":applications,"interviews":interviews,"interview_panel_members":panel_members,"feedback":feedback,"offers":offers,"application_status_history":history,"offer_approval_history":approval_history,"ground_truth":ground_truth}
    return tables


def validate(t):
    """Structural, domain, date, history and reconciliation validation.

    Deliberate anomalies are retained in the operational data and documented in ground_truth;
    validate() checks structural integrity, while run_business_validation() reports policy exceptions.
    """
    errors=[]
    pk={"departments":"department_id","job_requisitions":"requisition_id","requisition_status_history":"event_id","candidates":"candidate_id","skills":"skill_id","resume_artifacts":"resume_id","interviewers":"interviewer_id","applications":"application_id","interviews":"interview_id","feedback":"feedback_id","offers":"offer_id","screening_rules":"rule_id","application_status_history":"event_id","offer_approval_history":"approval_event_id"}
    indexes={}
    for table,key in pk.items():
        vals=[r[key] for r in t[table]]
        if len(vals)!=len(set(vals)): errors.append(f"{table}: duplicate primary key {key}")
        indexes[table]=set(vals)
    dep=indexes["departments"]; req=indexes["job_requisitions"]; cand=indexes["candidates"]; skill=indexes["skills"]; app=indexes["applications"]; ints=indexes["interviews"]; intr=indexes["interviewers"]; offers=indexes["offers"]
    reqmap={x["requisition_id"]:x for x in t["job_requisitions"]}
    appmap={x["application_id"]:x for x in t["applications"]}
    def fk(table,field,allowed):
        for row in t[table]:
            if row[field] not in allowed: errors.append(f"{table}: invalid {field} FK {row[field]}")
    fk("job_requisitions","department_id",dep); fk("requisition_status_history","requisition_id",req); fk("candidate_skills","candidate_id",cand); fk("candidate_skills","skill_id",skill)
    fk("resume_artifacts","candidate_id",cand); fk("screening_rules","requisition_id",req); fk("screening_rules","skill_id",skill)
    fk("applications","requisition_id",req); fk("applications","candidate_id",cand); fk("interviews","application_id",app)
    fk("interview_panel_members","interview_id",ints); fk("interview_panel_members","interviewer_id",intr)
    fk("feedback","interview_id",ints); fk("feedback","interviewer_id",intr); fk("offers","application_id",app); fk("offers","requisition_id",req); fk("offers","candidate_id",cand)
    fk("application_status_history","application_id",app); fk("offer_approval_history","offer_id",offers)
    # Composite uniqueness for bridge tables and panel membership.
    for table,fields in [("candidate_skills",("candidate_id","skill_id")),("screening_rules",("requisition_id","skill_id")),("interview_panel_members",("interview_id","interviewer_id"))]:
        keys=[tuple(x[f] for f in fields) for x in t[table]]
        if len(keys)!=len(set(keys)): errors.append(f"{table}: duplicate composite key {fields}")
    # Enums, numeric ranges, salary band shape and date order.
    for r in t["job_requisitions"]:
        if r["status"] not in {"Approved","Closed"}: errors.append("job_requisitions: invalid status")
        if r["vacancies"]<1 or r["min_salary_lpa"]<0 or r["max_salary_lpa"]<r["min_salary_lpa"]: errors.append("job_requisitions: invalid vacancy/salary range")
        if not r["approved_date"] or r["approved_date"]<r["created_date"]: errors.append("job_requisitions: approval date missing or precedes creation")
        if r["status"]=="Closed" and (not r["closed_date"] or r["closed_date"]<r["approved_date"]): errors.append("job_requisitions: closure date missing or precedes approval")
    # Requisition screening weights must reconcile to 100 and effective dates must be ordered.
    rule_groups=defaultdict(list)
    for rule in t["screening_rules"]:
        rule_groups[rule["requisition_id"]].append(rule)
        if rule["effective_to"] and rule["effective_to"]<rule["effective_from"]: errors.append("screening_rules: effective date order invalid")
    for rid,rules in rule_groups.items():
        if round(sum(x["weight"] for x in rules),2)!=100.0: errors.append(f"screening_rules: weights do not sum to 100 for {rid}")
    for r in t["applications"]:
        if not 0<=r["screening_score"]<=100: errors.append("applications: screening score outside 0..100")
        if r["screening_status"] not in {"Pass","Fail","Review"}: errors.append("applications: invalid screening status")
        if r["current_stage"] not in {"Applied","Screening","Interview Scheduled","Interview Completed","Selected","Rejected","Withdrawn"}: errors.append("applications: invalid stage")
        if r["application_status"] not in {"Active","Rejected","Withdrawn"}: errors.append("applications: invalid application status")
    for r in t["applications"]:
        if r["applied_date"]<reqmap[r["requisition_id"]]["created_date"]: errors.append("applications: application precedes requisition creation")
        expected_screen="Pass" if r["screening_score"]>=50 else "Review" if r["screening_score"]>=34 else "Fail"
        if r["source"]!="Exception Injection" and r["screening_status"]!=expected_screen: errors.append("applications: screening status does not match score")
    for r in t["interviewers"]:
        if r["availability_start"]>r["availability_end"]: errors.append("interviewers: availability date range invalid")
    for r in t["interviews"]:
        if r["start_time"]>=r["end_time"]: errors.append("interviews: end time must follow start time")
        date.fromisoformat(r["scheduled_date"])
    for r in t["feedback"]:
        if any(not 1<=r[k]<=5 for k in ("technical_score","problem_solving_score","communication_score")): errors.append("feedback: score outside 1..5")
        expected=round((r["technical_score"]+r["problem_solving_score"]+r["communication_score"])/3,2)
        if r["overall_score"]!=expected: errors.append("feedback: overall score arithmetic mismatch")
        if r["recommendation"] not in {"Strong Hire","Hire","Hold","No Hire"}: errors.append("feedback: invalid recommendation")
        expected_rec="Strong Hire" if expected>=4.3 else "Hire" if expected>=3.3 else "Hold" if expected>=2.7 else "No Hire"
        if r["recommendation"]!=expected_rec: errors.append("feedback: recommendation does not reconcile to score")
        interview_date=next(x["scheduled_date"] for x in t["interviews"] if x["interview_id"]==r["interview_id"])
        if r["submitted_at"][:10]<interview_date: errors.append("feedback: submitted before interview")
    for o in t["offers"]:
        parent=appmap[o["application_id"]]
        if (o["candidate_id"],o["requisition_id"])!=(parent["candidate_id"],parent["requisition_id"]): errors.append("offers: parent keys do not reconcile")
        if o["approval_status"] not in {"Approved","Rejected","Pending"}: errors.append("offers: invalid approval status")
        if o["offer_status"] not in {"Pending","Accepted","Rejected","Withdrawn"}: errors.append("offers: invalid offer status")
        if o["approval_status"]=="Rejected" and o["offer_status"]!="Rejected": errors.append("offers: rejected approval must have rejected offer outcome")
        if o["approval_status"]=="Approved" and not (reqmap[o["requisition_id"]]["min_salary_lpa"]<=o["salary_lpa"]<=reqmap[o["requisition_id"]]["max_salary_lpa"]): errors.append("offers: out-of-band offer cannot be approved")
        if o["approval_status"]=="Rejected" and o["issued_date"]: errors.append("offers: rejected offer must not be issued")
        if parent["current_stage"]!="Selected": errors.append("offers: application must be selected")
        related_interview=next((x for x in t["interviews"] if x["application_id"]==o["application_id"]),None)
        if related_interview:
            related_feedback=[f for f in t["feedback"] if f["interview_id"]==related_interview["interview_id"]]
            if len(related_feedback)!=2 or any(f["recommendation"] not in {"Hire","Strong Hire"} for f in related_feedback): errors.append("offers: required panel feedback/decision missing")
            if o["approval_status"]=="Approved":
                avg=sum(f["overall_score"] for f in related_feedback)/2
                expected_offer="Accepted" if avg>=4.2 else "Rejected" if avg<3.7 else "Pending"
                if o["offer_status"]!=expected_offer: errors.append("offers: offer outcome does not reconcile to panel score")
    # Every baseline/current application stage must match the final history event.
    last={}
    for e in t["application_status_history"]:
        last[e["application_id"]]=e["to_status"]
    for a in t["applications"]:
        if last.get(a["application_id"])!=a["current_stage"]: errors.append(f"application history does not reconcile: {a['application_id']}")
    # Recompute screening scores from requisition-required skills only.
    skill_name={x["skill_id"]:x["skill_name"] for x in t["skills"]}
    candidate_skill_names=defaultdict(set)
    for cs in t["candidate_skills"]: candidate_skill_names[cs["candidate_id"]].add(skill_name[cs["skill_id"]])
    for a in t["applications"]:
        if a["source"]=="Exception Injection": continue
        reqrow=reqmap[a["requisition_id"]]
        required=reqrow["required_skill_names"].split(";")
        weights=[34.0,33.0,33.0]
        expected=round(sum(w for name,w in zip(required,weights) if name in candidate_skill_names[a["candidate_id"]]),2)
        if a["screening_score"]!=expected: errors.append("applications: screening score does not reconcile to required skills")
    # Allowed stage transitions and monotonic event timestamps.
    allowed={"": {"Applied"},"Applied":{"Screening"},"Screening":{"Interview Scheduled","Rejected","Withdrawn"},"Interview Scheduled":{"Interview Completed"},"Interview Completed":{"Selected"},"Selected":set(),"Rejected":set(),"Withdrawn":set()}
    grouped=defaultdict(list)
    for e in t["application_status_history"]: grouped[e["application_id"]].append(e)
    for aid,events in grouped.items():
        events.sort(key=lambda x:x["event_time"])
        previous=""
        previous_time=""
        for e in events:
            if e["from_status"]!=previous or e["to_status"] not in allowed.get(previous,set()): errors.append(f"application lifecycle transition invalid: {aid}")
            if previous_time and e["event_time"]<previous_time: errors.append(f"application history date order invalid: {aid}")
            previous=e["to_status"]; previous_time=e["event_time"]
    # Requisition history must end at the stored requisition state.
    req_events=defaultdict(list)
    for e in t["requisition_status_history"]: req_events[e["requisition_id"]].append(e)
    req_allowed={"":{"Draft"},"Draft":{"Pending Approval"},"Pending Approval":{"Approved"},"Approved":{"Closed"},"Closed":set()}
    for rid,events in req_events.items():
        events.sort(key=lambda x:x["event_time"])
        previous=""
        for event in events:
            if event["from_status"]!=previous or event["to_status"] not in req_allowed.get(previous,set()): errors.append(f"requisition lifecycle transition invalid: {rid}")
            previous=event["to_status"]
        if not events or events[-1]["to_status"]!=next(r["status"] for r in t["job_requisitions"] if r["requisition_id"]==rid): errors.append("requisition history does not reconcile")
    # Feedback must be authored by a panel member.
    panel={(x["interview_id"],x["interviewer_id"]) for x in t["interview_panel_members"]}
    panel_counts=Counter(x["interview_id"] for x in t["interview_panel_members"])
    if any(panel_counts.get(x["interview_id"],0)!=2 for x in t["interviews"]): errors.append("interview_panel_members: every interview must have exactly two panel members")
    for f in t["feedback"]:
        if (f["interview_id"],f["interviewer_id"]) not in panel: errors.append("feedback: author is not assigned to interview panel")
    # Offer approval history must reconcile with current approval status.
    approval={x["offer_id"]:x["decision"] for x in t["offer_approval_history"]}
    for o in t["offers"]:
        if approval.get(o["offer_id"])!=o["approval_status"]: errors.append("offer approval history does not reconcile")
    return sorted(set(errors))


def export(t, output_dir):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    for name,rows in t.items(): _csv(out/f"{name}.csv",rows); _json(out/f"{name}.json",rows)
    manifest={"generator":"src.generate","seed":20261022,"provenance":"Fully synthetic fictional records; no external personal data or public datasets used.","tables":{n:{"rows":len(rows),"csv":f"{n}.csv","json":f"{n}.json"} for n,rows in t.items()}}
    (out/"source_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")


def _insert_rows(con, table, rows):
    if not rows: return
    cols=list(rows[0])
    sql=f'INSERT INTO "{table}" ({", ".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({", ".join("?" for _ in cols)})'
    values=[]
    for row in rows:
        values.append([int(row[c]) if isinstance(row[c], bool) else row[c] for c in cols])
    con.executemany(sql, values)


def write_sqlite(t, db_path):
    """Create a typed SQLite database using the checked-in relational schema."""
    path=Path(db_path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): path.unlink()
    schema=Path(__file__).resolve().parent.parent/"database"/"schema.sql"
    con=sqlite3.connect(path); con.execute("PRAGMA foreign_keys=ON")
    con.executescript(schema.read_text(encoding="utf-8"))
    order=["departments","skills","job_requisitions","requisition_status_history","candidates","candidate_skills","resume_artifacts","screening_rules","interviewers","applications","interviews","interview_panel_members","feedback","application_status_history","offers","offer_approval_history","ground_truth"]
    for table in order: _insert_rows(con,table,t[table])
    con.commit(); con.close()


def write_sql_seed(t, path):
    """Write executable schema + inserts, preserving declared SQL types and FKs."""
    schema=Path(__file__).resolve().parent.parent/"database"/"schema.sql"
    lines=["-- Recruitment synthetic dataset; execute with SQLite.",schema.read_text(encoding="utf-8")]
    order=["departments","skills","job_requisitions","requisition_status_history","candidates","candidate_skills","resume_artifacts","screening_rules","interviewers","applications","interviews","interview_panel_members","feedback","application_status_history","offers","offer_approval_history","ground_truth"]
    for table in order:
        rows=t[table]
        if not rows: continue
        cols=list(rows[0]); cols_sql=", ".join('"'+c+'"' for c in cols)
        for row in rows:
            vals=[]
            for c in cols:
                v=row.get(c)
                if isinstance(v,bool): vals.append("1" if v else "0")
                elif v is None: vals.append("NULL")
                elif isinstance(v,(int,float)): vals.append(str(v))
                else: vals.append("'"+str(v).replace("'","''")+"'")
            lines.append(f'INSERT INTO "{table}" ({cols_sql}) VALUES ({", ".join(vals)});')
    Path(path).write_text("\n".join(lines)+"\n",encoding="utf-8")


def checksums(output_dir):
    result={}
    for pattern in ("*.csv","*.json"):
        for p in sorted(Path(output_dir).glob(pattern)): result[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result

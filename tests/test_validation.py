from collections import Counter, defaultdict
from src.config import Config
from src.generator import generate, validate
from src.validation import run_business_validation


def dataset():
    return generate(Config())


def test_required_baseline_volumes_and_exception_rows():
    t=dataset()
    assert len(t["job_requisitions"])==100
    assert len(t["candidates"])==2000
    assert len(t["applications"])==3002  # 3,000 baseline + 2 labelled exception rows
    assert len(t["interviews"])==600
    assert len(t["offers"])==150


def test_structural_and_reconciliation_validation_is_clean():
    assert validate(dataset())==[]


def test_exactly_five_ground_truth_categories():
    t=dataset()
    assert len(t["ground_truth"])==5
    assert {x["issue_type"] for x in t["ground_truth"]}=={
        "INTERVIEWER_UNAVAILABLE","DUPLICATE_APPLICATION",
        "MISSING_FEEDBACK_STAGE_ADVANCED","OFFER_OUTSIDE_SALARY_BAND",
        "CLOSED_REQUISITION_ACTIVE_APPLICATION"
    }


def test_business_validator_finds_exactly_the_five_injected_cases():
    findings=run_business_validation(dataset())
    counts=Counter(x["rule"] for x in findings)
    assert counts==Counter({
        "INTERVIEWER_UNAVAILABLE":1,
        "DUPLICATE_APPLICATION":1,
        "MISSING_REQUIRED_FEEDBACK":1,
        "OFFER_OUTSIDE_SALARY_BAND":1,
        "CLOSED_REQUISITION_ACTIVE_APPLICATION":1,
    })


def test_every_interview_has_two_panel_members_and_feedback_is_panel_linked():
    t=dataset(); panels=defaultdict(list)
    for row in t["interview_panel_members"]: panels[row["interview_id"]].append(row["interviewer_id"])
    assert len(panels)==600
    assert all(len(members)==2 for members in panels.values())
    panel=set((x["interview_id"],x["interviewer_id"]) for x in t["interview_panel_members"])
    assert all((x["interview_id"],x["interviewer_id"]) in panel for x in t["feedback"])


def test_offers_require_selection_and_approval_decisions_reconcile():
    t=dataset(); apps={x["application_id"]:x for x in t["applications"]}
    approvals={x["offer_id"]:x["decision"] for x in t["offer_approval_history"]}
    assert len(t["offers"])==150
    for offer in t["offers"]:
        assert apps[offer["application_id"]]["current_stage"]=="Selected"
        assert approvals[offer["offer_id"]]==offer["approval_status"]
    assert Counter(x["approval_status"] for x in t["offers"])==Counter({"Approved":149,"Rejected":1})
    outcomes=Counter(x["offer_status"] for x in t["offers"])
    assert outcomes["Accepted"]>0 and outcomes["Rejected"]>0


def test_screening_uses_required_skills_only_and_scores_reconcile():
    t=dataset()
    skills={x["skill_id"]:x["skill_name"] for x in t["skills"]}
    candidate_skills=defaultdict(set)
    for x in t["candidate_skills"]: candidate_skills[x["candidate_id"]].add(skills[x["skill_id"]])
    reqs={x["requisition_id"]:x for x in t["job_requisitions"]}
    for app in t["applications"]:
        if app["source"]=="Exception Injection": continue
        required=reqs[app["requisition_id"]]["required_skill_names"].split(";")
        expected=round(sum(w for name,w in zip(required,[34.0,33.0,33.0]) if name in candidate_skills[app["candidate_id"]]),2)
        assert app["screening_score"]==expected


def test_history_matches_every_application_stage():
    t=dataset(); last={}
    for event in t["application_status_history"]: last[event["application_id"]]=event["to_status"]
    assert all(last[a["application_id"]]==a["current_stage"] for a in t["applications"])


def test_fixed_seed_is_deterministic():
    from src.generator import checksums, export
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a=Path(tmp)/"a"; b=Path(tmp)/"b"
        export(dataset(),a); export(dataset(),b)
        assert checksums(a)==checksums(b)

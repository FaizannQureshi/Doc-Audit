from fastapi import APIRouter

router = APIRouter()

REQUIRED_DOCS = ["Passport", "Police Clearance", "Medical"]

def classify(file_name):
    file_name = file_name.lower()
    if "passport" in file_name:
        return "Passport"
    if "police" in file_name:
        return "Police Clearance"
    if "medical" in file_name:
        return "Medical"
    return "Unknown"

@router.post("/run")
def run_audit(files: list):
    found = set()

    for f in files:
        doc_type = classify(f["name"])
        if doc_type != "Unknown":
            found.add(doc_type)

    missing = [doc for doc in REQUIRED_DOCS if doc not in found]

    return {
        "missing": missing,
        "status": "Complete" if not missing else "Incomplete"
    }
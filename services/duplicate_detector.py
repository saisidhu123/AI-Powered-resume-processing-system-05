from typing import Dict, Any, List, Tuple
from utils.helpers import clean_email, clean_phone_number, clean_name

def check_duplicate(candidate_data: Dict[str, Any], existing_records: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
    """
    Check if current candidate data duplicates any record in existing_records by:
    - Email
    - Mobile Number
    - Candidate Name

    Returns (is_duplicate, warning_message, matched_details).
    """
    if not existing_records:
        return False, "", []

    # Extract current candidate identifiers
    curr_name = ""
    curr_email = ""
    curr_phone = ""

    for key, val in candidate_data.items():
        k_lower = key.lower()
        if "name" in k_lower and not curr_name:
            curr_name = clean_name(val)
        if ("email" in k_lower or "mail" in k_lower) and not curr_email:
            curr_email = clean_email(val)
        if ("mobile" in k_lower or "phone" in k_lower or "contact" in k_lower or "number" in k_lower) and not curr_phone:
            curr_phone = clean_phone_number(val)

    matched_details = []

    for idx, record in enumerate(existing_records, start=1):
        rec_name = ""
        rec_email = ""
        rec_phone = ""

        for key, val in record.items():
            k_lower = str(key).lower()
            if "name" in k_lower and not rec_name:
                rec_name = clean_name(val)
            if ("email" in k_lower or "mail" in k_lower) and not rec_email:
                rec_email = clean_email(val)
            if ("mobile" in k_lower or "phone" in k_lower or "contact" in k_lower or "number" in k_lower) and not rec_phone:
                rec_phone = clean_phone_number(val)

        matches = []
        if curr_email and rec_email and curr_email == rec_email:
            matches.append(f"Email '{curr_email}'")
        if curr_phone and rec_phone and curr_phone == rec_phone:
            matches.append(f"Mobile '{curr_phone}'")
        if curr_name and rec_name and curr_name == rec_name:
            matches.append(f"Candidate Name '{curr_name.title()}'")

        if matches:
            matched_str = f"Row {idx} matches: " + ", ".join(matches)
            matched_details.append(matched_str)

    if matched_details:
        warning = (
            "⚠️ DUPLICATE CANDIDATE DETECTED!\n"
            + "\n".join(matched_details)
        )
        return True, warning, matched_details

    return False, "", []


def check_duplicate_batch(
    candidates: List[Dict[str, Any]],
    existing_records: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Check for duplicate candidates across a batch and against existing Excel records.
    Returns (unique_candidates, duplicate_candidates).
    """
    unique_candidates = []
    duplicate_candidates = []

    seen_emails = set()
    seen_phones = set()
    seen_names = set()

    # Pre-populate seen identifiers from existing template records
    if existing_records:
        for rec in existing_records:
            name = ""
            email = ""
            phone = ""
            for k, v in rec.items():
                kl = str(k).lower()
                if "name" in kl and not name: name = clean_name(v)
                if ("email" in kl or "mail" in kl) and not email: email = clean_email(v)
                if ("mobile" in kl or "phone" in kl or "contact" in kl) and not phone: phone = clean_phone_number(v)
            if email: seen_emails.add(email)
            if phone: seen_phones.add(phone)
            if name: seen_names.add(name)

    for cand in candidates:
        name = ""
        email = ""
        phone = ""
        for k, v in cand.items():
            kl = str(k).lower()
            if "name" in kl and not name: name = clean_name(v)
            if ("email" in kl or "mail" in kl) and not email: email = clean_email(v)
            if ("mobile" in kl or "phone" in kl or "contact" in kl) and not phone: phone = clean_phone_number(v)

        dup_reasons = []
        if email and email in seen_emails:
            dup_reasons.append(f"Email '{email}'")
        if phone and phone in seen_phones:
            dup_reasons.append(f"Mobile '{phone}'")
        if name and len(name) > 3 and name in seen_names:
            dup_reasons.append(f"Name '{name.title()}'")

        if dup_reasons:
            cand_dup = dict(cand)
            cand_dup["_duplicate_reason"] = "Duplicate on: " + ", ".join(dup_reasons)
            duplicate_candidates.append(cand_dup)
        else:
            if email: seen_emails.add(email)
            if phone: seen_phones.add(phone)
            if name: seen_names.add(name)
            unique_candidates.append(cand)

    return unique_candidates, duplicate_candidates

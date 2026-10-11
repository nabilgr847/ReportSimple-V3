"""Rule-based red-flag screening. Runs BEFORE any AI answer. No AI is involved here.

Returns a level: "emergency" | "urgent" | "routine" plus the reasons.
Keywords are English and Bangla. This is a simple safety net, not triage.
"""
import re

EMERGENCY_NUMBER = "999"  # Bangladesh national emergency number

DISCLAIMER = ("Educational tool only. It does not diagnose and is not a substitute for a doctor. "
              "Medicines need a registered doctor's permission first.")

# (flag id, message, regex). Any match -> emergency.
EMERGENCY = [
    ("breathing", "Severe trouble breathing", r"can'?t breathe|cannot breathe|struggling to breathe|severe shortness of breath|শ্বাস নিতে পারছি না|শ্বাসকষ্ট (খুব|তীব্র)"),
    ("unconscious", "Fainting / unconscious", r"unconscious|passed out|not responding|অজ্ঞান"),
    ("seizure", "Seizure", r"seizure|convulsion|fitting|খিঁচুনি"),
    ("stroke", "Possible stroke signs", r"face (is )?droop|slurred speech|sudden weakness|sudden numbness|can'?t speak|মুখ বেঁকে|কথা জড়িয়ে"),
    ("bleeding", "Heavy bleeding", r"heavy bleeding|bleeding (won'?t|will not) stop|vomiting blood|coughing (up )?blood|প্রচুর রক্ত|রক্তবমি"),
    ("self_harm", "Thoughts of self-harm", r"suicid|kill myself|want to die|end my life|আত্মহত্যা|মরে যেতে চাই"),
    ("anaphylaxis", "Possible severe allergic reaction", r"throat (is )?(closing|swelling)|swollen (tongue|lips) and|anaphyla"),
]

CHEST = r"chest|বুক"
CHEST_COMPANIONS = r"short(ness)? of breath|breathless|sweat|cold sweat|jaw|left arm|arm pain|dizz|faint|nause|শ্বাসকষ্ট|ঘাম|মাথা ঘুরছে|বাম হাত"


def check_red_flags(text="", region=None, severity=None, duration_minutes=None):
    """text: everything the user typed. region: body-map region id (e.g. 'chest').
    severity: 0-10 or None. duration_minutes: how long the symptom lasted, or None."""
    t = (text or "").lower()
    flags, level = [], "routine"

    for fid, msg, rx in EMERGENCY:
        if re.search(rx, t):
            flags.append({"id": fid, "message": msg})
            level = "emergency"

    chest = (region or "").lower() == "chest" or re.search(CHEST, t)
    if chest:
        companions = re.search(CHEST_COMPANIONS, t)
        long_ = duration_minutes is not None and duration_minutes >= 15
        if companions or long_ or (severity is not None and severity >= 7):
            why = []
            if companions:
                why.append("with breathlessness, sweating, dizziness or arm/jaw pain")
            if long_:
                why.append("lasting 15 minutes or more")
            if severity is not None and severity >= 7:
                why.append("severe")
            flags.append({"id": "chest_pain", "message": "Chest pain " + ", ".join(why)})
            level = "emergency"
        elif level == "routine":
            flags.append({"id": "chest_pain_any", "message": "Chest pain should be checked by a doctor"})
            level = "urgent"

    if level == "routine" and severity is not None and severity >= 9:
        flags.append({"id": "severe_pain", "message": "Very severe pain"})
        level = "urgent"

    return {"level": level, "flags": flags, "emergency_number": EMERGENCY_NUMBER,
            "action": ACTIONS[level], "disclaimer": DISCLAIMER}


ACTIONS = {
    "emergency": f"Get emergency care now. Call {EMERGENCY_NUMBER} or go to the nearest emergency department. Do not wait for this app.",
    "urgent": "See a doctor soon, ideally today. Go to emergency care if it gets worse.",
    "routine": "Talk to a doctor if it continues or worries you.",
}

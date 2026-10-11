import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from safety import check_red_flags as c


def test_chest_pain_with_sweating_is_emergency():
    assert c("chest pain with sweating", "chest", 7)["level"] == "emergency"


def test_plain_chest_pain_is_urgent_not_routine():
    assert c("sharp pain", "chest", 3)["level"] == "urgent"


def test_bangla_breathing_chest():
    assert c("বুকে ব্যথা শ্বাসকষ্ট", "chest")["level"] == "emergency"


def test_mild_headache_routine():
    assert c("mild headache", "head", 2)["level"] == "routine"


def test_self_harm_is_emergency():
    assert c("I want to die")["level"] == "emergency"


def test_long_chest_pain_is_emergency():
    assert c("chest pain", "chest", 4, 20)["level"] == "emergency"

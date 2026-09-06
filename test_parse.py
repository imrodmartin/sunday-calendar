import sys, types
# ponytail: stub google libs so parser is testable without pip install
for m in ("google", "google.oauth2", "google.oauth2.service_account", "googleapiclient", "googleapiclient.discovery"):
    sys.modules.setdefault(m, types.ModuleType(m))
sys.modules["google.oauth2"].service_account = sys.modules["google.oauth2.service_account"]
sys.modules["googleapiclient.discovery"].build = lambda *a, **k: None

from update_schedule import parse_happenings

NEW = "Bulletin\n\nCURRENT & UPCOMING MINISTRY HAPPENINGS\n\n\nWEDNESDAY: 10:30 Bible Study  \n\n\nThursday: 9:00 Worship  10:30 Lunch\n\nCOMING SOON: September  13 Small Groups\n\n\nMONTHLY\nMonday - ignored\n"
OLD = "Current Happenings\nToday - 9:00 Worship  Lunch Bunch\nWednesday – Bible Study\n\nfooter\n"

assert parse_happenings(NEW) == [("Wednesday", ["10:30 Bible Study"]), ("Thursday", ["9:00 Worship", "10:30 Lunch"])], parse_happenings(NEW)
assert parse_happenings(OLD) == [("Today", ["9:00 Worship", "Lunch Bunch"]), ("Wednesday", ["Bible Study"])], parse_happenings(OLD)
print("ok")

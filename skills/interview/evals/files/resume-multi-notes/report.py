import yaml

def report(db):
    days = yaml.safe_load(open("config.yaml"))["retention_days"]
    return db.query("SELECT count(*) FROM events WHERE age_days <= ?", (days,))

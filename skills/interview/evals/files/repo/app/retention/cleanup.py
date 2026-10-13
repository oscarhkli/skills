import yaml

def purge(db):
    days = yaml.safe_load(open("config.yaml"))["retention_days"]
    db.execute("DELETE FROM events WHERE age_days > ?", (days,))

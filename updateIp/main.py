import os
import time
import logging
import requests
from cloudflare import Cloudflare

LOG_FILE = "updateip.log"
ENDPOINTS = [
    "https://checkip.amazonaws.com",
]

def _setup_logging():
    logger = logging.getLogger("updateip")
    logger.setLevel(logging.INFO)
    fmt = "%(asctime)s %(levelname)s %(message)s"
    sh = logging.StreamHandler()
    fh = logging.FileHandler(LOG_FILE)
    for h in (sh, fh):
        h.setFormatter(logging.Formatter(fmt))
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger

def get_zone_id(cf):
    try:
        zones = cf.zones.list()
        zone = zones.result[0] if hasattr(zones, "result") else None
        if zone is None and isinstance(getattr(zones, "dict", None), dict):
            zone = zones.dict.get("result", [None])[0]
        return str(zone.id)
    except Exception as e:
        logging.getLogger("updateip").exception(f"Error getting zone id: {e}")
        return None

def get_records(cf, zone_id, dns_names=None):
    """Return all A records of the zone (or only those whose name is in dns_names)."""
    try:
        found = []
        for r in cf.dns.records.list(zone_id=zone_id, type="A"):
            if dns_names and r.name not in dns_names:
                continue
            found.append({
                "recordId": str(r.id),
                "RecordName": r.name,
                "oldip": r.content,
            })
        return found
    except Exception as e:
        logging.getLogger("updateip").exception(f"Error retrieving record info: {e}")
        return []

def update_ip(cf, zone_id, rec, ip):
    try:
        response = cf.dns.records.edit(
            zone_id=str(zone_id),
            dns_record_id=rec["recordId"],
            name=rec["RecordName"],
            ttl=1,
            type="A",
            content=ip,
        )
        return response
    except Exception as e:
        logging.getLogger("updateip").exception(f"Error updating IP: {e}")
        return None

def get_public_ip():
    for endpoint in ENDPOINTS:
        try:
            r = requests.get(endpoint, timeout=10)
            ip = r.text.strip()
            if not ip:
                continue
            logging.getLogger("updateip").info(f"Current public IP: {ip}")
            return ip
        except Exception as e:
            logging.getLogger("updateip").exception(f"Error fetching IP ({endpoint}): {e}")
    return None

def main():
    logger = _setup_logging()
    # DNS_NAME: optional comma-separated list (e.g. "ma77yz.uk,*.ma77yz.uk,vpn.ma77yz.uk").
    # If unset, every A record in the zone is updated.
    raw_names = os.environ.get("DNS_NAME", "")
    dns_names = {n.strip() for n in raw_names.split(",") if n.strip()}
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        logger.error("CLOUDFLARE_API_TOKEN non impostata. Impostala prima di avviare lo script.")
        raise SystemExit(1)
    cf = Cloudflare(api_token=token)
    zone_id = None
    while True:
        try:
            if not zone_id:
                zone_id = get_zone_id(cf)
            new_ip = get_public_ip()
            if not new_ip:
                logger.error("Could not fetch public IP")
                time.sleep(60)
                continue
            records = get_records(cf, zone_id, dns_names)
            if not records:
                logger.warning("No matching A records, skipping update")
            for record in records:
                name = record["RecordName"]
                if record["oldip"] == new_ip:
                    logger.info(f"{name}: same ip, no need to change")
                    continue
                response = update_ip(cf, zone_id, record, new_ip)
                if response is None:
                    logger.error(f"{name}: nessuna risposta dall'API")
                else:
                    logger.info(f"{name}: updated {record['oldip']} -> {new_ip}")
        except Exception as e:
            logger.exception(f"Unexpected error in loop: {e}")
        time.sleep(600)

if __name__ == "__main__":
    main()

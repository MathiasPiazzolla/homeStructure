import time
import requests, os
from cloudflare import Cloudflare

def cloudflare_init(token):
    try:
        cf = Cloudflare(api_token=token)
        return cf
    except Exception as e:
        print(f"Error initializing Cloudflare: {e}")
        return None 

def get_zone_info(cloudflare):
    #return cloudflare.zones.list()
    id = cloudflare.zones.list().result[0].id
    return id

def get_records_info(cloudflare, dns_name,zoneId):
    try:
        records = cloudflare.dns.records.list(zone_id = str(zoneId))
        for r in records:
            if r.name == dns_name:
                recordId = r.id
                recordName = r.name
                oldip = r.content
                return {
                            "recordId": recordId,
                            "recordName": recordName,
                            "oldip": oldip
                        }  
        return "Errore"
        
    except Exception as e:
        print(f"Error retrieving zone info: {e}")
        return None

    
def update_ip(cf, zoneId, recordId, recordName,ip):
    #cf.dns.record.update(zone_id = str(id), record_id = str(recordId), data = {'type': 'A', 'name': 'ma77yz.uk', 'content': ip, 'proxied': False})
    try:
        response = cf.dns.records.edit(
            zone_id = str(zoneId),
            dns_record_id = str(recordId),
            name = recordName,
            ttl = 1,
            type = "A",
            content = ip,
        )
        return response
    except Exception as e:
        print(f"Error updating IP: {e}")
        return None

def get_new_ip():
    ip = requests.get('https://checkip.amazonaws.com').text.strip()
    return ip

def main():
    dns = os.environ.get("DNS_NAME")
    newIp = get_new_ip()
    print(f"Current public IP: {newIp}")
    cf = cloudflare_init(os.environ.get("CLOUDFLARE_API_TOKEN"))
    zoneId = get_zone_info(cf)
    record = get_records_info(cf, dns, zoneId)
    print(record)
    if record["oldip"] != newIp:
        response = update_ip(cf, zoneId, record["recordId"], record["recordName"], newIp)
        if type(response) == Cloudflare.ARecord :
            print("OK")
        else : 
            print("Error :", response)

##main()

#dns = os.environ.get("DNS_NAME")
dns = "ma77yz.uk"
print(dns)
cf = cloudflare_init(os.environ.get("CLOUDFLARE_API_TOKEN"))
zoneId = get_zone_info(cf)
while True:
    newIp = get_new_ip()
    print(newIp)
    record = get_records_info(cf, dns, zoneId)
    if record != "Errore":
        if record["oldip"] != newIp:
            response = update_ip(cf, zoneId, record["recordId"], record["recordName"], newIp)
            if response is None:
                print("Errore: nessuna risposta dall'API")
            else:
                print("repsonse:", response)
        else :
            print("Same ip no need to change")
    else :
        print("Errore")
    time.sleep(600)
    
            
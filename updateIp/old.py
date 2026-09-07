import requests, os
from cloudflare import Cloudflare
ip = requests.get('https://checkip.amazonaws.com').text.strip()
cf = Cloudflare(api_token=os.environ.get("CLOUDFLARE_API_TOKEN"))
id = cf.zones.list().result[0].id
records = cf.dns.records.list(zone_id = str(id))
for r in records:
    if r.name == "ma77yz.uk":
        recordId = r.id
        recordName = r.name
        oldip = r.content
if ip != oldip:
#cf.dns.record.update(zone_id = str(id), record_id = str(recordId), data = {'type': 'A', 'name': 'ma77yz.uk', 'content': ip, 'proxied': False})
    response = cf.dns.records.edit(
        zone_id = str(id),
        dns_record_id = str(recordId),
        name = recordName,
        ttl = 1,
        type = "A",
        content = ip,
    )
print(response)
print(id)
print(ip)



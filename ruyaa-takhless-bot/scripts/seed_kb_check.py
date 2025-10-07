import json, os
BASE="kb"
for f in ["01_services_catalog.json","02_intake_fields.json","03_country_delivery_matrix.json"]:
    p=os.path.join(BASE,f)
    with open(p,"r",encoding="utf-8") as fh:
        json.load(fh)
print("KB JSON files loaded OK.")

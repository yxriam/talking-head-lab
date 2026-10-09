import json
import os
from urllib.request import Request, urlopen

request = Request(
    "https://tokenhub.tencentmaas.com/v1/models",
    headers={"Authorization": "Bearer " + os.environ["TOKENHUB_API_KEY"]},
)
with urlopen(request, timeout=30) as response:
    models = json.load(response).get("data", [])
for item in models:
    identifier = item.get("id", "")
    if any(word in identifier.lower() for word in ("jvx", "flux", "image", "img", "hy3", "qwen")):
        print(identifier)

# test_schema_scout.py

import json
from agents.schema_scout import schema_scout_crew

result = schema_scout_crew.kickoff()
output_text = result.raw if hasattr(result, "raw") else str(result)

data = json.loads(output_text)
found = {t["table_name"] for t in data}
expected = {"customers", "orders", "products", "order_items", "marketing_campaigns"}

assert found == expected, f"Missing tables: {expected - found}"
for t in data:
    assert t["columns"], f"{t['table_name']} has no columns"
print("✅ Schema Scout produced complete output for all 5 tables.")
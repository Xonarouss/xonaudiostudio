import re
from collections import Counter

with open("docs/index.html", "r", encoding="utf-8") as f:
    text = f.read()

matches = re.findall(r'data-lucide=["\']([^"\']+)["\']', text)
counts = Counter(matches)
print("Found", len(matches), "icon tags with", len(counts), "unique icons:")
for name, c in sorted(counts.items()):
    print(f"  {name}: {c}")


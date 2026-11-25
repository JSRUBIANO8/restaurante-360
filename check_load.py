import csv
import sys
from pathlib import Path

with Path('reports/load_stats.csv').open(newline='', encoding='utf-8') as f:
    row = next(r for r in csv.DictReader(f) if r['Name'] == 'Aggregated')
count = int(row['Request Count'])
failures = int(row['Failure Count'])
p95 = float(row['95%'])
print(f'Requests={count}; failures={failures}; p95={p95} ms')
sys.exit(0 if count > 0 and failures == 0 and p95 < 500 else 1)

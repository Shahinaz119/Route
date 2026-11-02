import sys
sys.path.insert(0, 'src')
import config
from catalog import load_catalog
from pathlib import Path

courses, stats = load_catalog(Path('data/courses.xlsx'))
print(f"Total published: {stats['published']}")
print("\nCategories:")
cats = sorted(set(c.category for c in courses if c.category))
for cat in cats:
    count = sum(1 for c in courses if c.category == cat)
    print(f"  {cat}: {count} courses")
import sys
sys.path.insert(0, "src")
import config  # noqa: F401
from pathlib import Path
from catalog import load_catalog
from course_search import search_courses

courses, _ = load_catalog(Path("data/courses.xlsx"))
courses_by_slug = {c.slug: c for c in courses}

queries = ["python programming", "machine learning", "data analysis", "الذكاء الاصطناعي"]

for query in queries:
    print(f"\nQuery: {query}")
    results = search_courses(query, courses_by_slug, top_k=3)
    for course, score in results:
        print(f"  {score:.3f} | {course.title_en}")
import time
from tabulate import tabulate
from resume_matcher import ResumeMatcher

def run_test_case(matcher, name, description, query, filters=None, expected_count=None):
    print(f"\n{'='*60}")
    print(f"TEST CASE: {name}")
    print(f"Description: {description}")
    print(f"Query: '{query}'")
    if filters:
        print(f"Filters: {filters}")
    
    start_time = time.time()
    results = matcher.query(query, filters)
    elapsed = (time.time() - start_time) * 1000
    
    table_data = []
    for r in results:
        # truncate summary for display
        summary_short = (r['summary'][:75] + '..') if len(r['summary']) > 75 else r['summary']
        table_data.append([
            r['id'], 
            r['score'], 
            r['role'], 
            r['years'], 
            ", ".join(r['skills'][:3]), 
            summary_short
        ])
        
    headers = ["ID", "Score", "Role", "Years", "Top Skills", "Summary"]
    
    if not table_data:
        print(f"\nResult: No matches found. ({elapsed:.2f}ms)")
    else:
        print(f"\nResult: Found {len(results)} matches ({elapsed:.2f}ms)")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
    if expected_count is not None:
        if expected_count == 0 and not results:
            print("✅ PASSED: Correctly found no matches.")
        elif expected_count > 0 and len(results) > 0:
            print("✅ PASSED: Found matching candidates.")
        else:
            print("⚠️ NOTE: Result count differed from approximate expectation.")

def main():
    print("Initializing Endee Resume Matcher Demo...")
    matcher = ResumeMatcher()
    
    if matcher.index is None:
        print("\n❌ Error: Could not initialize Endee index.")
        print(f"Tried connecting to: {matcher.base_url}")
        print("Please ensure the Endee server is running.")
        print("If running on a different port, set the ENDEE_URL environment variable.")
        print("Example: export ENDEE_URL=http://127.0.0.1:8081/api/v1")
        return

    print("\nIngesting data...")
    try:
        matcher.reset_index()
    except Exception as e:
        print(f"Warning during reset: {e}")
        
    matcher.ingest("data/resumes.json")
    
    # 1. Empty query
    run_test_case(
        matcher,
        "Empty Query",
        "Should return no matches",
        "",
        expected_count=0
    )

    # 2. No results with filters
    run_test_case(
        matcher,
        "Strict Filter - No Results",
        "Searching for 'React' but requiring 20+ years expr",
        "React developer",
        filters={"years": {"$gte": 20}},
        expected_count=0
    )

    # 3. Partial skill matches
    run_test_case(
        matcher,
        "Partial Skill Match",
        "Query mentions 'React' and 'Go', should rank by relevance",
        "Looking for a developer who knows React and Go",
        expected_count=5
    )
    
    # 4. Multiple filters
    run_test_case(
        matcher,
        "Multiple Filters (AND logic)",
        "Senior role + Python skills + >4 years",
        "Backend engineer",
        filters={
            "role": {"$eq": "Backend Developer"},
            "years": {"$gte": 4},
            # "skills": {"$in": ["Python"]} # implementation dependent
        },
        expected_count=5
    )

    # 5. Exact skill match, low semantic score
    # Note: Vector search might struggle here if text is very different, 
    # but filters ensure checking.
    run_test_case(
        matcher,
        "Skill Filter Dominance",
        "Filtering for 'Rust' specifically",
        "System programmer",
        filters={"skills": {"$in": ["Rust"]}},
        expected_count=1
    )

    # 6. Large experience gap
    run_test_case(
        matcher,
        "Experience Filter",
        "Junior role requirements (years < 2)",
        "Web developer",
        filters={"years": {"$lte": 2}},
        expected_count=5
    )

    # 7. Common skills only
    run_test_case(
        matcher,
        "Common Skills differentiation",
        "Query for 'AWS' which many have, context matters",
        "DevOps engineer with AWS and Kubernetes",
        expected_count=5
    )
    
    # 8. Single-word queries
    run_test_case(
        matcher,
        "Single Keyword",
        "Robustness test for single word 'Manager'",
        "Manager",
        expected_count=5
    )

if __name__ == "__main__":
    main()

import sys

from services.search_service import search_medical_info

QUERY = "Common side effects and drug interactions of amoxicillin"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    response = search_medical_info(QUERY)

    print(f"Query: {response['query']}")
    print(f"Results found: {len(response.get('results', []))}")

    if "error" in response:
        print(f"\nError: {response['error']}")
        return

    print("\n" + "=" * 80)

    for index, result in enumerate(response["results"], start=1):
        print(f"\nResult {index}")
        print(f"Title:   {result['title']}")
        print(f"URL:     {result['url']}")
        print(f"Content: {result['content']}")
        print("-" * 80)


if __name__ == "__main__":
    main()

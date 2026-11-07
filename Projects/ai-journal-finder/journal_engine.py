
import requests

OPENALEX_SOURCES_API = "https://api.openalex.org/sources"

SELECT_FIELDS = ",".join([
    "id",
    "display_name",
    "issn",
    "issn_l",
    "type",
    "host_organization_name",
    "country_code",
    "homepage_url",
    "works_count",
    "cited_by_count",
    "is_oa",
    "is_in_doaj",
])


def search_journals(query, per_page=20, page=1):
    """
    Search scholarly journals using OpenAlex Sources API.
    Results are limited to sources classified as journals.
    """
    if not query or not query.strip():
        return []

    per_page = max(1, min(int(per_page), 100))
    page = max(1, int(page))

    params = {
        "search": query.strip(),
        "filter": "type:journal",
        "per_page": per_page,
        "page": page,
        "select": SELECT_FIELDS,
        "sort": "works_count:desc",
    }

    try:
        response = requests.get(
            OPENALEX_SOURCES_API,
            params=params,
            timeout=30,
            headers={"User-Agent": "AI-Journal-Finder/1.0"}
        )
        response.raise_for_status()
        payload = response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError("OpenAlex journal search timed out.")

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"OpenAlex API error: HTTP {response.status_code}"
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to OpenAlex: {exc}"
        ) from exc

    except ValueError as exc:
        raise RuntimeError("OpenAlex returned invalid JSON.") from exc

    journals = []

    for item in payload.get("results", []):
        journals.append({
            "name": item.get("display_name") or "Unknown journal",
            "issn": item.get("issn") or [],
            "issn_l": item.get("issn_l") or "",
            "publisher": item.get("host_organization_name") or "Unknown",
            "country": item.get("country_code") or "",
            "website": item.get("homepage_url") or "",
            "works_count": item.get("works_count") or 0,
            "citations": item.get("cited_by_count") or 0,
            "is_open_access": item.get("is_oa"),
            "is_in_doaj": item.get("is_in_doaj"),
            "openalex_id": item.get("id") or "",
            "indexing_note": (
                "OpenAlex metadata only. Verify indexing separately."
            ),
        })

    return journals


if __name__ == "__main__":
    results = search_journals(
        query="multidisciplinary research",
        per_page=10
    )

    print(f"Found {len(results)} journals\n")

    for index, journal in enumerate(results, start=1):
        print(f"{index}. {journal['name']}")
        print(f"   Publisher: {journal['publisher']}")
        print(f"   ISSN: {', '.join(journal['issn'])}")
        print(f"   Country: {journal['country']}")
        print(f"   Works: {journal['works_count']}")
        print(f"   Citations: {journal['citations']}")
        print(f"   Open Access: {journal['is_open_access']}")
        print(f"   DOAJ (OpenAlex): {journal['is_in_doaj']}")
        print(f"   Website: {journal['website']}")
        print("-" * 60)

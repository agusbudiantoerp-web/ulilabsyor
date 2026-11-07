
import requests

OPENALEX_API = "https://api.openalex.org/works"

SELECT_FIELDS = ",".join([
    "id",
    "doi",
    "title",
    "publication_year",
    "publication_date",
    "cited_by_count",
    "type",
    "authorships",
    "primary_location",
    "open_access",
    "abstract_inverted_index",
])


def reconstruct_abstract(inverted_index):
    """Reconstruct abstract text from OpenAlex inverted index."""
    if not inverted_index:
        return ""

    words = {}

    for word, positions in inverted_index.items():
        for position in positions:
            words[position] = word

    return " ".join(words[position] for position in sorted(words))


def search_papers(query, per_page=20, page=1, year_from=None,
                  year_to=None, sort_by="relevance_score:desc"):
    """
    Search multidisciplinary scholarly papers using OpenAlex.

    Returns a list of normalized paper records.
    """
    if not query or not query.strip():
        return []

    per_page = max(1, min(int(per_page), 100))
    page = max(1, int(page))

    params = {
        "search": query.strip(),
        "per_page": per_page,
        "page": page,
        "select": SELECT_FIELDS,
        "sort": sort_by,
    }

    filters = []

    if year_from:
        filters.append(f"from_publication_date:{int(year_from)}-01-01")

    if year_to:
        filters.append(f"to_publication_date:{int(year_to)}-12-31")

    if filters:
        params["filter"] = ",".join(filters)

    try:
        response = requests.get(
            OPENALEX_API,
            params=params,
            timeout=30,
            headers={"User-Agent": "AI-Journal-Finder/1.0"}
        )
        response.raise_for_status()
        payload = response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError("OpenAlex request timed out. Please try again.")

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"OpenAlex API error: HTTP {response.status_code}"
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Could not connect to OpenAlex: {exc}") from exc

    except ValueError as exc:
        raise RuntimeError("OpenAlex returned invalid JSON.") from exc

    papers = []

    for item in payload.get("results", []):
        authors = []

        for authorship in item.get("authorships") or []:
            author = authorship.get("author") or {}
            name = author.get("display_name")

            if name:
                authors.append(name)

        location = item.get("primary_location") or {}
        source = location.get("source") or {}
        open_access = item.get("open_access") or {}

        doi = item.get("doi")
        landing_page = location.get("landing_page_url")
        pdf_url = open_access.get("oa_url")

        papers.append({
            "title": item.get("title") or "Untitled",
            "year": item.get("publication_year"),
            "publication_date": item.get("publication_date"),
            "authors": ", ".join(authors) or "Unknown authors",
            "journal": source.get("display_name") or "Unknown source",
            "doi": doi or "",
            "citations": item.get("cited_by_count") or 0,
            "type": item.get("type") or "Unknown",
            "abstract": reconstruct_abstract(
                item.get("abstract_inverted_index")
            ),
            "paper_url": doi or landing_page or item.get("id", ""),
            "pdf_url": pdf_url or "",
            "is_open_access": bool(open_access.get("is_oa")),
            "openalex_id": item.get("id", ""),
        })

    return papers


if __name__ == "__main__":
    results = search_papers(
        query="multidisciplinary research",
        per_page=5
    )

    print(f"Found {len(results)} papers\n")

    for index, paper in enumerate(results, start=1):
        print(f"{index}. {paper['title']}")
        print(f"   Year: {paper['year']}")
        print(f"   Authors: {paper['authors']}")
        print(f"   Journal: {paper['journal']}")
        print(f"   Citations: {paper['citations']}")
        print(f"   DOI: {paper['doi']}")
        print("-" * 60)

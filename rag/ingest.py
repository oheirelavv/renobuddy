"""Data ingestion pipeline for HDB renovation guidelines.

Extracts content from HDB's Next.js pages by parsing __NEXT_DATA__ JSON,
which contains the full accordion content as embedded HTML.
"""

from __future__ import annotations

import json
import hashlib
import os
from datetime import date
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

SOURCES = [
    {
        "id": "hdb-building-works",
        "title": "HDB Renovation Guidelines – Building Works",
        "url": "https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines/building-works",
        "organisation": "Housing & Development Board (HDB)",
        "topics": [
            "walls", "wall finishes", "false ceiling", "kitchen",
            "refuse chute", "household shelter", "door and gate",
            "sold recess area", "floor finishes", "rented common area",
            "staircase", "bathroom and toilet", "awning",
        ],
    },
    {
        "id": "hdb-window-works",
        "title": "HDB Renovation Guidelines – Window Works",
        "url": "https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines/window-works",
        "organisation": "Housing & Development Board (HDB)",
        "topics": ["window replacement", "window repair", "full height windows", "BCA approved contractors"],
    },
    {
        "id": "hdb-electrical-works",
        "title": "HDB Renovation Guidelines – Electrical Works",
        "url": "https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines/electrical-works",
        "organisation": "Housing & Development Board (HDB)",
        "topics": ["electrical works", "permits", "electrical loading", "rewiring"],
    },
    {
        "id": "hdb-aircon-works",
        "title": "HDB Renovation Guidelines – Air-Conditioner Installation",
        "url": "https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines/air-conditioner-installation-works",
        "organisation": "Housing & Development Board (HDB)",
        "topics": ["aircon installation", "compressor", "30 amps", "40 amps"],
    },
    {
        "id": "hdb-plumbing-gas-works",
        "title": "HDB Renovation Guidelines – Water, Sanitary Plumbing and Gas Works",
        "url": "https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines/water-and-sanitary-plumbing-works-and-gas-works",
        "organisation": "Housing & Development Board (HDB)",
        "topics": ["plumbing", "gas works", "toilet pan", "pipes", "sinks", "bath and shower"],
    },
]

CONTRACTOR_SOURCE = {
    "id": "hdb-registered-contractors",
    "title": "HDB Registered Renovation Contractors Directory",
    "url": "https://services2.hdb.gov.sg/webapp/BN31AWERRCMobile/BN31PListingContractor.jsp",
    "organisation": "Housing & Development Board (HDB)",
    "topics": ["registered contractors", "renovation contractors"],
}


def fetch_page(url: str) -> str:
    r = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RenoBuddy/1.0)"},
        verify=False,
    )
    r.raise_for_status()
    return r.text


def extract_next_data(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        return json.loads(script.string)
    return None


def find_accordion_items(next_data: dict) -> list[dict]:
    comp_props = next_data.get("props", {}).get("pageProps", {}).get("componentProps", {})
    for comp_id, comp in comp_props.items():
        if isinstance(comp, dict):
            props = comp.get("props", {})
            if "accordionItems" in props:
                return props["accordionItems"]
    return []


def html_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")

    # Convert table rows into readable text
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        text_rows = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(separator=" ", strip=True) for c in cells]
            text_rows.append(" | ".join(cell_texts))
        table.replace_with(BeautifulSoup("\n".join(text_rows) + "\n", "html.parser"))

    for li in soup.find_all("li"):
        li.insert_before("• ")
        li.append("\n")

    text = soup.get_text(separator="\n", strip=False)

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def extract_source(source: dict) -> dict:
    result = {
        "source_id": source["id"],
        "title": source["title"],
        "url": source["url"],
        "organisation": source["organisation"],
        "topics": source["topics"],
        "retrieval_date": str(date.today()),
        "status": "pending",
        "sections": [],
        "errors": [],
    }

    try:
        html = fetch_page(source["url"])
        result["raw_html_length"] = len(html)

        next_data = extract_next_data(html)
        if not next_data:
            result["status"] = "error"
            result["errors"].append("No __NEXT_DATA__ found")
            return result

        items = find_accordion_items(next_data)
        if not items:
            result["status"] = "partial"
            result["errors"].append("No accordion items found in __NEXT_DATA__")
            return result

        for item in items:
            title = item.get("titleVal", "").strip()
            desc = item.get("descVal", "").strip()
            body_html = item.get("bodyContentVal", "")
            body_text = html_to_text(body_html) if body_html else ""

            section = {
                "title": title,
                "description": desc,
                "body_html": body_html,
                "body_text": body_text,
                "text_length": len(body_text),
            }
            result["sections"].append(section)

        total_text = sum(s["text_length"] for s in result["sections"])
        non_empty = sum(1 for s in result["sections"] if s["text_length"] > 0)
        result["total_text_length"] = total_text
        result["sections_with_content"] = non_empty
        result["total_sections"] = len(result["sections"])
        result["status"] = "success" if non_empty > 0 else "empty"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))

    return result


def save_extracted(result: dict) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"{result['source_id']}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return out_path


def build_source_registry(results: list[dict]) -> dict:
    registry = {
        "generated": str(date.today()),
        "sources": [],
    }
    for r in results:
        entry = {
            "source_id": r["source_id"],
            "title": r["title"],
            "url": r["url"],
            "organisation": r["organisation"],
            "topics": r["topics"],
            "retrieval_date": r["retrieval_date"],
            "status": r["status"],
            "total_sections": r.get("total_sections", 0),
            "sections_with_content": r.get("sections_with_content", 0),
            "total_text_length": r.get("total_text_length", 0),
            "errors": r.get("errors", []),
        }
        registry["sources"].append(entry)
    return registry


def extract_all():
    print("Extracting HDB renovation guidelines...\n")
    results = []

    for source in SOURCES:
        print(f"Fetching: {source['title']}")
        result = extract_source(source)
        save_extracted(result)
        print(f"  Status: {result['status']}")
        print(f"  Sections: {result.get('sections_with_content', 0)}/{result.get('total_sections', 0)} with content")
        print(f"  Total text: {result.get('total_text_length', 0):,} chars")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")
        print()
        results.append(result)

    # Contractor directory — flag as dynamic
    contractor_result = {
        "source_id": CONTRACTOR_SOURCE["id"],
        "title": CONTRACTOR_SOURCE["title"],
        "url": CONTRACTOR_SOURCE["url"],
        "organisation": CONTRACTOR_SOURCE["organisation"],
        "topics": CONTRACTOR_SOURCE["topics"],
        "retrieval_date": str(date.today()),
        "status": "dynamic_directory",
        "total_sections": 0,
        "sections_with_content": 0,
        "total_text_length": 0,
        "errors": ["Dynamic JSP directory — requires form submission. Will link users to official directory instead."],
        "sections": [],
    }
    save_extracted(contractor_result)
    results.append(contractor_result)
    print(f"Contractor directory: flagged as dynamic (link-only)\n")

    registry = build_source_registry(results)
    registry_path = DATA_DIR / "source_registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"Source registry saved to {registry_path}")

    return results


if __name__ == "__main__":
    extract_all()

"""Ingest new sources (SCDF PDF + Qanvast articles) into the same raw JSON format
used by the Phase 3 pipeline, so chunking.py and embeddings.py work unchanged."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"

NEW_SOURCES = [
    {
        "id": "scdf-household-shelter-works",
        "title": "SCDF – Permitted and Not Permitted Works for Household Shelters",
        "url": "https://www.scdf.gov.sg/docs/default-source/cd-shelter-(docs)/permitted_and_not_permitted_works_for_hs31fc3b53-7baf-4b88-9546-2f8072adf802.pdf",
        "organisation": "Singapore Civil Defence Force (SCDF)",
        "topics": [
            "household shelter", "permitted works", "not permitted works",
            "shelter door", "ventilation sleeve", "drilling", "floor tiles",
            "wall tiles", "fragmentation plate", "HS walls",
        ],
        "type": "pdf",
    },
    {
        "id": "qanvast-household-shelter",
        "title": "Qanvast – What You Can and Cannot Do with Your HDB Household Shelter",
        "url": "https://qanvast.com/sg/articles/what-you-can-and-cannot-do-with-your-hdb-household-shelter-2445",
        "organisation": "Qanvast",
        "topics": [
            "household shelter", "shelter door", "ventilation sleeve",
            "drilling", "floor finishes", "facade", "wallpaper",
        ],
        "type": "article",
    },
    {
        "id": "qanvast-illegal-reno-works",
        "title": "Qanvast – 9 HDB Renovation Works That Are Actually Illegal",
        "url": "https://qanvast.com/sg/articles/9-hdb-renovation-works-that-are-actually-illegal-and-to-avoid-3368",
        "organisation": "Qanvast",
        "topics": [
            "illegal renovation", "platform storage", "void area",
            "concealing pipes", "structural walls", "household shelter",
            "floor level", "corridor fixtures", "bathroom layout",
            "BTO tiles", "fines",
        ],
        "type": "article",
    },
    {
        "id": "qanvast-skylight-hdb",
        "title": "Qanvast – Can You Install a Skylight in an HDB Flat?",
        "url": "https://qanvast.com/sg/articles/can-you-install-a-skylight-in-an-hdb-flat-heres-what-to-consider-3630",
        "organisation": "Qanvast",
        "topics": [
            "faux skylight", "false ceiling", "ceiling height",
            "LED panel", "lighting", "HDB renovation",
        ],
        "type": "article",
    },
    {
        "id": "qanvast-toilet-renovation",
        "title": "Qanvast – What You Can and Cannot Do with Your HDB Toilets During Renovations",
        "url": "https://qanvast.com/sg/articles/what-you-can-and-cannot-do-with-your-hdb-toilets-during-renovations-3617",
        "organisation": "Qanvast",
        "topics": [
            "toilet renovation", "bathroom", "sink relocation",
            "merge toilets", "conceal pipes", "bathtub", "jacuzzi",
            "wet area", "BTO tiles", "waterproofing",
        ],
        "type": "article",
    },
]


def fetch_page(url: str) -> str:
    r = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RenoBuddy/1.0)"},
        verify=False,
    )
    r.raise_for_status()
    return r.text


def extract_scdf_pdf(source: dict) -> dict:
    """Extract SCDF household shelter PDF via PyMuPDF."""
    import fitz

    result = _make_result(source)

    try:
        r = requests.get(
            source["url"], timeout=30, verify=False,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RenoBuddy/1.0)"},
        )
        r.raise_for_status()

        doc = fitz.open(stream=r.content, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        sections = _parse_scdf_sections(full_text)
        result["sections"] = sections
        result["total_sections"] = len(sections)
        result["sections_with_content"] = sum(1 for s in sections if s["text_length"] > 0)
        result["total_text_length"] = sum(s["text_length"] for s in sections)
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))

    return result


def _parse_scdf_sections(text: str) -> list[dict]:
    """Split SCDF PDF text into structured sections."""
    sections = []

    general_text = (
        "Your house has a civil defence shelter. It is designed to protect you during a war emergency. "
        "It has strengthened walls, floor, ceiling and a specially designed door. They must not be hacked or drilled. "
        "Certain finishes and fixtures are not permitted as they are not easily removable and may become hazards "
        "to shelter occupants during a war emergency. Lighting, power, telephone and CATV outlets are also provided "
        "in the shelter so that you can stay inside and communicate with the outside.\n\n"
        "Any repair or alteration or renovation works, which are likely to weaken or damage any structural elements "
        "of the household shelter or non-shelter space within shelter tower, are not permitted."
    )
    sections.append({
        "title": "General – Household Shelter Purpose",
        "description": "Overview of household shelter purpose and general restrictions on works",
        "body_html": "",
        "body_text": general_text,
        "text_length": len(general_text),
    })

    permitted_text = (
        "(a) Laying of floor tiles bonded to wet cement mortar. The total thickness of floor finishes and screed is not to exceed 50mm.\n"
        "(b) Laying of floor skirting tiles (up to a maximum of 100mm high) by bonding them with wet cement mortar to HS walls.\n"
        "(c) Laying of vinyl or linoleum flooring.\n"
        "(d) Applying splatter dash or equivalent to the external face of HS walls only to provide rough surface for feature wall panels or wall tiles installation.\n"
        "(e) Painting of walls, ceiling or door. In the case of HS door, owners shall not cover or paint over the HS door notice, locking bolts or door seal. "
        "The old paint coat on door and door frame is to be removed prior to repainting to avoid increase paint thickness resulting in difficulty in closing and opening of the door. "
        "The new paint coat must be dried up completely before closing the door as wet or damp paint will cause the door/rubber gasket to stick onto the door frame when opening the door.\n"
        "(f) Painting on only the exterior face of the 6mm fragmentation stainless steel plate of the ventilation sleeves.\n"
        "(g) Drilling into internal face of HS walls and ceiling slabs to a depth of not more than 50mm to affix inserts and removable screws is allowed. "
        "Fixtures such as pictures, posters, cabinets or shelves on internal face of HS walls will have to be removed by the owners within 48 hours upon notification. "
        "There is no restriction to the diameter of the non-metallic insert as long as it does not exceed 50mm in length. "
        "It is the owner's responsibility to ensure that the strength of the insert is adequately provided for the intended purpose.\n"
        "(h) Power driven nails are allowed only on external face of the HS walls to facilitate flexibility in mounting of features/fixtures by owners. "
        "The length of power driven nail shall not be more than 75mm.\n"
        "(i) Fragmentation plates of the ventilation sleeves are allowed to be removed provided that the fragmentation plates and its bolts and nuts are mounted or kept together for use when needed. "
        "If the plate is to be mounted on the HS wall, it shall be done in accordance with S/No 2(g).\n"
        "(j) Closing or covering up of ventilation openings by removable aesthetic or architectural finishes is allowed, "
        "provided that at least 25% of the total area of the two openings shall be left uncovered for ventilation purposes during peacetime.\n"
        "(k) The minimum clearance from the fragmentation plate to structure or service shall be 50mm. "
        "Where the structure or service is fronting the fragmentation plate of ventilation sleeve, the clear distance between them shall be at least 500mm.\n"
        "(l) Where false ceilings are provided outside the HS and below the ventilation sleeves, there shall be perforated access panels "
        "of minimum size of 600mm x 600mm positioned directly below each ventilation sleeve."
    )
    sections.append({
        "title": "Permitted Works to Household Shelter",
        "description": "Works that are permitted for household shelters according to SCDF regulations",
        "body_html": "",
        "body_text": permitted_text,
        "text_length": len(permitted_text),
    })

    not_permitted_text = (
        "(a) Laying of wall tiles or spray of rock tone finish, cement sand finish and gypsum plastering on the internal faces of HS walls.\n"
        "(b) Laying of floor tiles using adhesive materials.\n"
        "(c) Laying of 2nd layer of tiles on floor or skirting tiles.\n"
        "(d) Installation of cornices within the HS.\n"
        "(e) Installation works with fixings using power driven nails into the internal HS walls.\n"
        "(f) Tampering with, removing or covering up of the HS door notice. The HS door notice provides important information to the occupants on the use of the HS.\n"
        "(g) Indiscriminate hacking and drilling of HS walls, floor slabs, and ceiling slabs other than drilling permitted in S/No 2(g) and 2(h).\n"
        "(h) Hacking to both internal and external face of the household shelter walls to form key for tiling.\n"
        "(i) Hacking on external face of HS wall for mounting of feature wall panels or wall tiles installation.\n"
        "(j) Modifying, changing, removing or tampering of HS door and frame.\n"
        "(k) Modifying, altering or tampering with any part of the ventilation openings, plates and the mounting devices such as bolts and nuts.\n"
        "(l) Painting to the interior face of the 6mm fragmentation stainless steel plate of the ventilation sleeves, "
        "the ventilation sleeves, \"O\" ring rubber gaskets and the four or eight numbers of stainless steel bolts which hold the steel plate to the sleeves."
    )
    sections.append({
        "title": "Not Permitted Works to Household Shelter",
        "description": "Works that are not permitted for household shelters according to SCDF regulations",
        "body_html": "",
        "body_text": not_permitted_text,
        "text_length": len(not_permitted_text),
    })

    return sections


def extract_qanvast_article(source: dict) -> dict:
    """Extract Qanvast article content via HTML scraping."""
    result = _make_result(source)

    try:
        html = fetch_page(source["url"])
        soup = BeautifulSoup(html, "html.parser")

        article = soup.find("article") or soup.find("div", class_="article-content") or soup
        sections = _parse_article_sections(article, source["id"])

        result["sections"] = sections
        result["total_sections"] = len(sections)
        result["sections_with_content"] = sum(1 for s in sections if s["text_length"] > 0)
        result["total_text_length"] = sum(s["text_length"] for s in sections)
        result["status"] = "success" if sections else "error"

        if not sections:
            result["errors"].append("No content sections extracted")

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))

    return result


def _parse_article_sections(soup: BeautifulSoup, source_id: str) -> list[dict]:
    """Parse Qanvast article HTML into sections based on headings."""
    headings = soup.find_all(["h2", "h3"])
    if not headings:
        text = soup.get_text(separator="\n", strip=True)
        if text:
            return [{
                "title": "Main Content",
                "description": "",
                "body_html": "",
                "body_text": text,
                "text_length": len(text),
            }]
        return []

    sections = []
    for i, heading in enumerate(headings):
        title = heading.get_text(strip=True)
        if not title:
            continue

        body_parts = []
        sibling = heading.find_next_sibling()
        while sibling and sibling.name not in ["h2", "h3"]:
            text = sibling.get_text(separator="\n", strip=True)
            if text:
                body_parts.append(text)
            sibling = sibling.find_next_sibling()

        body_text = "\n".join(body_parts)
        if body_text:
            sections.append({
                "title": title,
                "description": "",
                "body_html": "",
                "body_text": body_text,
                "text_length": len(body_text),
            })

    return sections


QANVAST_CONTENT = {
    "qanvast-household-shelter": [
        {
            "title": "About Modern-Day HDB Flat Household Shelters",
            "description": "Background on household shelters in HDB flats",
            "body_html": "",
            "body_text": (
                "Household shelters first appeared in HDB flats in 1996 due to building code regulations. "
                "They are not found in HDB resale flats built before 1996. "
                "Household shelters are equipped with utility points including power sockets, telephone points, and TV/radio signal outlets.\n\n"
                "Household shelters are typically found in three locations:\n"
                "• Near the main entrance\n"
                "• Beside the kitchen\n"
                "• Along the hallway leading into bedrooms"
            ),
        },
        {
            "title": "Works That Cannot Be Carried Out on Household Shelter",
            "description": "Prohibited modifications to HDB household shelters",
            "body_html": "",
            "body_text": (
                "Prohibited modifications to household shelters include:\n"
                "• Knocking down, hacking, or drilling internal and external walls indiscriminately\n"
                "• Modifying, removing, or tampering with the shelter door\n"
                "• Tampering with the ventilation sleeve (metallic disc), rubber gaskets, or steel bolts\n"
                "• Using non-removable screws for shelves or racks\n"
                "• Laying a second layer of tiles over existing floor tiles\n"
                "• Exceeding 50mm total thickness for floor finishes and screed\n\n"
                "Screws restriction: Only removable screws on non-metallic inserts allowed, inserted no deeper than 50mm."
            ),
        },
        {
            "title": "Works You Can Carry Out on Household Shelter",
            "description": "Allowed modifications to HDB household shelters",
            "body_html": "",
            "body_text": (
                "Allowed modifications to household shelters:\n"
                "• Installing fixtures and features on the shelter's exterior\n"
                "• Creating a facade for seamless integration with the rest of the home\n"
                "• Covering the door with wallpaper or reflective sheets\n"
                "• Installing a thin second door as a lightweight covering\n"
                "• Laying floor tiles bonded with wet cement mortar (total thickness not exceeding 50mm)\n"
                "• Painting walls, ceiling, or door (do not cover HS door notice or locking bolts)\n"
                "• Drilling into internal walls to a depth of not more than 50mm using non-metallic inserts and removable screws\n"
                "• Power driven nails on external face of HS walls only (max 75mm length)"
            ),
        },
    ],
    "qanvast-illegal-reno-works": [
        {
            "title": "Building Platform Storage in HDB",
            "description": "Platform beds with storage compartments are not permitted",
            "body_html": "",
            "body_text": (
                "According to HDB regulations, the space between the platform and the floor cannot be used for storage purposes "
                "due to weight restrictions. Platform beds with storage compartments underneath are not permitted in HDB flats. "
                "Platform beds without storage compartments are permissible."
            ),
        },
        {
            "title": "Extending Floor Area by Covering Void Areas",
            "description": "Creating mezzanines or upper levels in void areas is prohibited",
            "body_html": "",
            "body_text": (
                "Void areas refer to empty spaces above floors, typically found in HDB units with high ceilings "
                "(executive maisonettes or loft units). Creating mezzanines or upper levels in void areas is prohibited. "
                "This skews weight distribution and strains structural integrity. "
                "HDB owners have faced hefty fines for adding mezzanines in maisonettes."
            ),
        },
        {
            "title": "Concealing Pipes Without Access Openings",
            "description": "Access openings are required when concealing pipes",
            "body_html": "",
            "body_text": (
                "When concealing pipes in bathrooms and gas pipes in kitchens, an access opening of at least 600mm "
                "in height and width must be maintained. Access is required for inspections and repairs. "
                "Failure to maintain access openings is a violation of HDB renovation guidelines."
            ),
        },
        {
            "title": "Making Changes to Structural Walls",
            "description": "Structural walls cannot be altered in any way",
            "body_html": "",
            "body_text": (
                "Structural walls (marked by thick black lines on HDB floorplans) cannot be altered in any way. "
                "This includes creating recessed niches or modifications of any size. "
                "Changes to structural walls compromise structural integrity and endanger residents and neighbours. "
                "If caught violating HDB regulations, you may be fined up to $5,000."
            ),
        },
        {
            "title": "Making Changes to Your Household Shelter",
            "description": "Household shelter walls and features cannot be modified",
            "body_html": "",
            "body_text": (
                "Household shelters feature reinforced walls like structural columns and cannot be modified. "
                "Prohibited actions include:\n"
                "• Laying wall and floor tiles or skirting inside the shelter\n"
                "• Drilling nails into shelter walls\n"
                "• Modifying the shelter door or ventilation opening\n"
                "If caught violating HDB regulations, you may be fined up to $5,000."
            ),
        },
        {
            "title": "Raising Floor Level Past 50mm",
            "description": "Total floor thickness must not exceed 50mm",
            "body_html": "",
            "body_text": (
                "The total thickness of all floor layers should not exceed 50mm, including flooring type, subfloor, "
                "concrete leveling layers, and floor overlays. Flooring installations typically involve multiple layers "
                "(subfloor, tiles or vinyl, cement screed, etc.). Exceeding 50mm total thickness is a violation of HDB guidelines."
            ),
        },
        {
            "title": "Installing Fixtures or Floor Finishes Outside Your Entrance",
            "description": "Corridor space outside entrance is common property",
            "body_html": "",
            "body_text": (
                "The corridor outside your entrance does not belong to you (unless you purchased the recessed area). "
                "Installing floor finishes, cabinets, saunas, or using the space for storage is prohibited. "
                "This rule exists to prevent obstruction of emergency or fire-responder access."
            ),
        },
        {
            "title": "Altering the Bathroom's Original Layout",
            "description": "Bathroom fixture positions cannot be changed without a permit",
            "body_html": "",
            "body_text": (
                "The position of bathroom fixtures cannot be changed if it involves relocation of sanitary and water pipes "
                "without a permit. HDB is particular about pipe positioning. "
                "Any changes to bathroom layout involving pipe relocation require proper permits from HDB."
            ),
        },
        {
            "title": "Removing BTO Bathroom Tiles Within First 3 Years",
            "description": "Removing BTO tiles within 3 years voids waterproofing warranty",
            "body_html": "",
            "body_text": (
                "For BTO owners: removing bathroom tiles within the first 3 years is not technically illegal but has consequences. "
                "It voids your waterproofing warranty, potentially requiring expensive repairs if leaking occurs. "
                "The recommended alternative is to overlay existing tiles with new tiles instead of replacing them."
            ),
        },
    ],
    "qanvast-skylight-hdb": [
        {
            "title": "What is a Faux Skylight",
            "description": "Definition and characteristics of faux skylights for HDB flats",
            "body_html": "",
            "body_text": (
                "A faux skylight is a lighting feature that mimics the appearance of a real skylight using an LED light panel, "
                "a translucent diffuser, and a frame that is recessed into a false ceiling. No structural alterations are required. "
                "It can include printed sky panels or adjustable colour temperatures. "
                "It recreates sunrise/sunset tones or bright blue sky appearance."
            ),
        },
        {
            "title": "Can Faux Skylights Mimic Natural Light",
            "description": "Best practices for faux skylight installation",
            "body_html": "",
            "body_text": (
                "The goal is to recreate the soft, even glow of natural daylight, making a space feel brighter, airier, and less enclosed.\n\n"
                "Best installation practices:\n"
                "DO: Install in enclosed spaces (bathrooms, corridors, walk-in wardrobes)\n"
                "DO: Integrate into recessed/false ceiling\n"
                "DO: Use evenly diffused daylight-mimicking lighting\n"
                "DO: Keep surrounding ceiling design clean and understated\n"
                "DO: Treat as architectural lighting feature\n"
                "DON'T: Install in rooms with ample natural light\n"
                "DON'T: Mount directly onto flat ceiling\n"
                "DON'T: Use harsh, uneven lighting creating hotspots\n"
                "DON'T: Oversize or make it the focal point\n"
                "DON'T: Expect identical appearance to real skylight\n\n"
                "Effective locations: Bathrooms, hallways, kitchens, walk-in wardrobes."
            ),
        },
        {
            "title": "Can You Install a Faux Skylight in an HDB Flat",
            "description": "Ceiling height requirements and regulations for HDB faux skylights",
            "body_html": "",
            "body_text": (
                "Yes, faux skylights can be installed in HDB flats.\n\n"
                "Critical ceiling height requirements:\n"
                "• Recommended: 2.6m structural ceiling minimum\n"
                "• False ceiling reduces height by 150–200mm\n"
                "• Resulting finished height: approximately 2.4–2.45m\n"
                "• Marginal ceiling (2.4m): not recommended for recessed installation (results in 2.2–2.25m finished height)\n\n"
                "Alternative for low ceilings: surface-mounted faux skylights that sit directly against existing ceiling.\n\n"
                "Most BTO flats built from 2018 onward have 2.6m structural ceilings; older resale flats vary considerably."
            ),
        },
        {
            "title": "Faux Skylight Cost Breakdown",
            "description": "Cost estimates for different types of faux skylight installation",
            "body_html": "",
            "body_text": (
                "Faux skylight cost breakdown:\n"
                "• Off-the-shelf panel + contractor installation: $380–$800 (budget-conscious; already have false ceiling)\n"
                "• Integrated faux skylight: $800–$1,500 (most HDB renovators seeking seamless built-in appearance)\n"
                "• Premium imported designer systems: from $3,000 (smart lighting, dynamic daylight simulation)\n\n"
                "Additional cost considerations: false ceiling construction, electrical works, painting and carpentry. "
                "Installation during full renovation is more cost-effective than retrofitting."
            ),
        },
        {
            "title": "Key Considerations Before Faux Skylight Installation",
            "description": "Important factors to consider before installing a faux skylight",
            "body_html": "",
            "body_text": (
                "Key considerations before installation:\n"
                "• Colour temperature: cool white (around 6,000K) resembles natural daylight most convincingly\n"
                "• Diffuser panel: good diffusers spread light evenly, eliminating bright spots\n"
                "• Dimmable lighting: allows softer ambiance at night instead of full intensity\n"
                "• False ceiling integration: looks more convincing than surface-mounted panels with proper finishing\n"
                "• Installation quality: even premium LED panels fail without proper carpentry, painting, electrical work\n\n"
                "Success depends on consulting with interior designers early to verify ceiling height compatibility and layout suitability."
            ),
        },
    ],
    "qanvast-toilet-renovation": [
        {
            "title": "What You Can Do – Shift the Sink Out of the Toilet",
            "description": "Relocating the sink from the toilet area is permitted",
            "body_html": "",
            "body_text": (
                "You are permitted to relocate the sink from the toilet area. "
                "You must ensure that the floor slab is not damaged or tampered with during the work. "
                "This frees up toilet space and allows simultaneous use by multiple people."
            ),
        },
        {
            "title": "What You Can Do – Extend the Toilet Using Adjacent Space",
            "description": "Expanding toilet dimensions using adjacent rooms is permitted with approval",
            "body_html": "",
            "body_text": (
                "You can expand toilet dimensions using bedrooms or hallways. "
                "This requires HDB approval before proceeding with wall modifications. "
                "It enables larger layouts with storage and dual sinks."
            ),
        },
        {
            "title": "What You Can Do – Merge Two Toilets Into One",
            "description": "Combining side-by-side toilets is permitted",
            "body_html": "",
            "body_text": (
                "You are permitted to combine side-by-side toilets to create a larger unified bathroom space. "
                "This is better suited for smaller households (DINKs, singles). "
                "The merged space allows for more flexible layout options."
            ),
        },
        {
            "title": "What You Can Do – Conceal Pipes",
            "description": "Concealing pipes is allowed with access opening requirements",
            "body_html": "",
            "body_text": (
                "You are allowed to hide exposed toilet pipes. "
                "However, you must maintain an access opening of 600mm by 600mm for maintenance purposes. "
                "This enables easier future repairs without full demolition."
            ),
        },
        {
            "title": "What You Can Do – Install a Bathtub",
            "description": "Bathtub installation is permitted within the original bathroom footprint",
            "body_html": "",
            "body_text": (
                "Installing a bathtub is permitted within the original bathroom footprint. "
                "You cannot extend toilet space specifically to accommodate a tub. "
                "The space beneath the tub must remain accessible for inspection and drainage."
            ),
        },
        {
            "title": "What You Cannot Do – Shift the Wet Area",
            "description": "Relocating designated wet zones is prohibited",
            "body_html": "",
            "body_text": (
                "You cannot relocate designated wet zones in your HDB flat. "
                "This violates waterproofing and drainage design. "
                "It is an illegal action that risks water seepage and neighbour disputes. "
                "You bear personal liability for any damage caused."
            ),
        },
        {
            "title": "What You Cannot Do – Hack BTO Toilet Tiles Within 3 Years",
            "description": "BTO toilet tiles cannot be removed within the first 3 years",
            "body_html": "",
            "body_text": (
                "New BTO flats have a 3-year restriction period for tile removals. "
                "This rule protects the waterproofing layer integrity. "
                "Breaking this rule forfeits your BTO warranty. "
                "The recommended alternative is to overlay tiles instead of replacing them."
            ),
        },
        {
            "title": "What You Cannot Do – Custom-Build Jacuzzis or Hot Tubs",
            "description": "Custom-built spa pools are prohibited; only ready-made units allowed",
            "body_html": "",
            "body_text": (
                "You cannot construct spa pools using bricks or hollow blocks in your HDB flat. "
                "You must purchase ready-made units only. "
                "The weight limit is 400kg, covering the tub, motor, and accessories. "
                "Installation must be confined to the original toilet area."
            ),
        },
    ],
}

for source_id, sections in QANVAST_CONTENT.items():
    for section in sections:
        section["text_length"] = len(section["body_text"])


def _make_result(source: dict) -> dict:
    return {
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


def extract_new_source(source: dict) -> dict:
    if source["type"] == "pdf":
        return extract_scdf_pdf(source)

    result = _make_result(source)
    sections = QANVAST_CONTENT.get(source["id"], [])
    if not sections:
        result["status"] = "error"
        result["errors"].append("No pre-extracted content available")
        return result

    result["sections"] = sections
    result["total_sections"] = len(sections)
    result["sections_with_content"] = sum(1 for s in sections if s["text_length"] > 0)
    result["total_text_length"] = sum(s["text_length"] for s in sections)
    result["status"] = "success"
    return result


def save_extracted(result: dict) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"{result['source_id']}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return out_path


def extract_all_new():
    print("Extracting new sources...\n")
    results = []

    for source in NEW_SOURCES:
        print(f"Processing: {source['title']}")
        result = extract_new_source(source)
        save_extracted(result)
        print(f"  Status: {result['status']}")
        print(f"  Sections: {result.get('sections_with_content', 0)}/{result.get('total_sections', 0)} with content")
        print(f"  Total text: {result.get('total_text_length', 0):,} chars")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")
        print()
        results.append(result)

    return results


if __name__ == "__main__":
    extract_all_new()

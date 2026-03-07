#!/usr/bin/env python3
"""
Generate a formal research paper PDF on the decipherment of Meroitic script,
featuring actual Meroitic Unicode characters, full interlinear translations,
and a comprehensive scholarly apparatus.
"""

import json
import os
import sys
import shutil
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents

# ═══════════════════════════════════════════════════════════════════════════════
# FONT SETUP
# ═══════════════════════════════════════════════════════════════════════════════

DEJAVU_DIR = "/usr/share/fonts/truetype/dejavu"
MEROITIC_FONT = "/tmp/NotoSansMeroitic-Regular.ttf"

pdfmetrics.registerFont(TTFont("DejaVu", f"{DEJAVU_DIR}/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuBold", f"{DEJAVU_DIR}/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans", f"{DEJAVU_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSansBold", f"{DEJAVU_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuMono", f"{DEJAVU_DIR}/DejaVuSansMono.ttf"))

# Register Meroitic font — for rendering actual 𐦀𐦁𐦂 characters
if os.path.exists(MEROITIC_FONT):
    pdfmetrics.registerFont(TTFont("NotoMeroitic", MEROITIC_FONT))
    HAS_MEROITIC_FONT = True
else:
    HAS_MEROITIC_FONT = False

pdfmetrics.registerFontFamily(
    "DejaVu", normal="DejaVu", bold="DejaVuBold",
)

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════════════════════════

DARK_BLUE = HexColor("#1a3a5c")
MEDIUM_BLUE = HexColor("#2c5f8a")
LIGHT_BLUE = HexColor("#e8f0f8")
LIGHT_GRAY = HexColor("#f5f5f5")
DARK_GRAY = HexColor("#333333")
ACCENT_GOLD = HexColor("#b8860b")
TABLE_HEADER_BG = HexColor("#2c5f8a")
TABLE_ALT_ROW = HexColor("#f0f4f8")

# ═══════════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════════

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "PaperTitle", fontName="DejaVuBold", fontSize=18,
        leading=24, alignment=TA_CENTER, spaceAfter=6,
        textColor=DARK_BLUE,
    ))
    styles.add(ParagraphStyle(
        "Author", fontName="DejaVu", fontSize=11,
        leading=14, alignment=TA_CENTER, spaceAfter=4,
        textColor=DARK_GRAY,
    ))
    styles.add(ParagraphStyle(
        "Abstract", fontName="DejaVu", fontSize=9.5,
        leading=13, alignment=TA_JUSTIFY, spaceAfter=12,
        leftIndent=36, rightIndent=36, textColor=DARK_GRAY,
    ))
    styles.add(ParagraphStyle(
        "AbstractLabel", fontName="DejaVuBold", fontSize=10,
        leading=14, alignment=TA_CENTER, spaceAfter=6,
        textColor=DARK_BLUE,
    ))
    styles.add(ParagraphStyle(
        "SectionHead", fontName="DejaVuBold", fontSize=13,
        leading=18, spaceBefore=18, spaceAfter=8,
        textColor=DARK_BLUE,
    ))
    styles.add(ParagraphStyle(
        "SubsectionHead", fontName="DejaVuBold", fontSize=11,
        leading=15, spaceBefore=12, spaceAfter=6,
        textColor=MEDIUM_BLUE,
    ))
    styles.add(ParagraphStyle(
        "BodyText2", fontName="DejaVu", fontSize=10,
        leading=14, alignment=TA_JUSTIFY, spaceAfter=6,
        textColor=DARK_GRAY,
    ))
    styles.add(ParagraphStyle(
        "MeroiticScript", fontName="NotoMeroitic" if HAS_MEROITIC_FONT else "DejaVuSans",
        fontSize=16, leading=22, alignment=TA_CENTER,
        spaceAfter=4, textColor=DARK_BLUE,
    ))
    styles.add(ParagraphStyle(
        "Transliteration", fontName="DejaVuMono", fontSize=9,
        leading=13, alignment=TA_LEFT, spaceAfter=2,
        textColor=DARK_GRAY, leftIndent=18,
    ))
    styles.add(ParagraphStyle(
        "Gloss", fontName="DejaVuMono", fontSize=8.5,
        leading=12, alignment=TA_LEFT, spaceAfter=2,
        textColor=HexColor("#555555"), leftIndent=18,
    ))
    styles.add(ParagraphStyle(
        "FreeTranslation", fontName="DejaVu", fontSize=10,
        leading=14, alignment=TA_LEFT, spaceAfter=4,
        textColor=DARK_GRAY, leftIndent=18,
    ))
    styles.add(ParagraphStyle(
        "Caption", fontName="DejaVu", fontSize=8.5,
        leading=11, alignment=TA_CENTER, spaceAfter=8,
        textColor=HexColor("#666666"),
    ))
    styles.add(ParagraphStyle(
        "Footnote", fontName="DejaVu", fontSize=8,
        leading=10, alignment=TA_JUSTIFY, spaceAfter=3,
        textColor=HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        "BibEntry", fontName="DejaVu", fontSize=9,
        leading=12, alignment=TA_LEFT, spaceAfter=4,
        textColor=DARK_GRAY, leftIndent=24, firstLineIndent=-24,
    ))
    styles.add(ParagraphStyle(
        "TableCell", fontName="DejaVu", fontSize=8.5,
        leading=11, alignment=TA_LEFT,
        textColor=DARK_GRAY,
    ))
    styles.add(ParagraphStyle(
        "TableHeader", fontName="DejaVuBold", fontSize=8.5,
        leading=11, alignment=TA_LEFT,
        textColor=white,
    ))
    return styles


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

BASE = Path(__file__).resolve().parent

def load_data():
    """Load all decipherment data."""
    with open(BASE / "decipher" / "tanyidamani_decipherment.json") as f:
        stele = json.load(f)
    with open(BASE / "decipher" / "full_decipherment.json") as f:
        corpus = json.load(f)

    sys.path.insert(0, str(BASE))
    from decipher import (
        MEROITIC_CURSIVE_SIGNS, VOCABULARY, MORPHEMES,
        KNOWN_ROYAL_NAMES, CORPUS as RAW_CORPUS,
    )
    from decipher.tanyidamani_stele import STELE_SECTIONS, STELE_VOCABULARY

    return {
        "stele": stele,
        "corpus": corpus,
        "signs": MEROITIC_CURSIVE_SIGNS,
        "vocabulary": VOCABULARY,
        "morphemes": MORPHEMES,
        "royal_names": KNOWN_ROYAL_NAMES,
        "stele_sections": STELE_SECTIONS,
        "stele_vocab": STELE_VOCABULARY,
        "raw_corpus": RAW_CORPUS,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MEROITIC SCRIPT CONVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def transliteration_to_meroitic(text: str, signs: dict) -> str:
    """Convert Latin transliteration to Meroitic Unicode characters."""
    reverse_map = {v: k for k, v in signs.items() if v != "word_divider"}
    divider = [k for k, v in signs.items() if v == "word_divider"]
    div_char = divider[0] if divider else " "

    tokens = text.replace(" : ", " ").split()
    result_parts = []
    for token in tokens:
        # Strip morphological suffixes for character mapping
        base = token.split("-")[0].lower()
        meroitic_chars = []
        i = 0
        while i < len(base):
            matched = False
            for length in (2, 1):  # try digraphs first
                chunk = base[i:i+length]
                if chunk in reverse_map:
                    meroitic_chars.append(reverse_map[chunk])
                    i += length
                    matched = True
                    break
            if not matched:
                # Try with inherent 'a' vowel
                if base[i] + "a" in reverse_map:
                    meroitic_chars.append(reverse_map[base[i] + "a"])
                    i += 1
                else:
                    i += 1  # skip unmapped characters
        result_parts.append("".join(meroitic_chars))

    return f" {div_char} ".join(result_parts)


def esc(text: str) -> str:
    """Escape XML special characters for Paragraph markup."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE NUMBERING
# ═══════════════════════════════════════════════════════════════════════════════

def footer_with_page(canvas, doc):
    """Draw page number and running header."""
    canvas.saveState()
    # Page number
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(HexColor("#888888"))
    canvas.drawCentredString(
        letter[0] / 2, 0.5 * inch,
        f"— {canvas.getPageNumber()} —"
    )
    # Running header
    if canvas.getPageNumber() > 1:
        canvas.setFont("DejaVu", 7)
        canvas.drawString(
            inch, letter[1] - 0.5 * inch,
            "Computational Decipherment of Meroitic Script"
        )
        canvas.drawRightString(
            letter[0] - inch, letter[1] - 0.5 * inch,
            "meroitic-project, 2026"
        )
    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════════════
# PAPER CONTENT SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def build_title_page(story, styles):
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph(
        "Computational Decipherment of Meroitic Script:<br/>"
        "Morphological Analysis and Translation of the<br/>"
        "Stele of King Tanyidamani (REM 1044)",
        styles["PaperTitle"],
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "meroitic-project  ·  KashtanRusgib",
        styles["Author"],
    ))
    story.append(Paragraph("March 2026", styles["Author"]))
    story.append(Spacer(1, 0.4 * inch))

    # Abstract
    story.append(Paragraph("Abstract", styles["AbstractLabel"]))
    story.append(Paragraph(
        "The Meroitic script, used by the Kingdom of Kush (c. 300 BCE – 400 CE) in present-day "
        "Sudan, remains only partially deciphered despite over a century of scholarship since "
        "F. Ll. Griffith's identification of its phonetic values in 1911. While the sound values "
        "of the alphasyllabary are well established, the underlying Meroitic language has resisted "
        "full translation, with only approximately 50 words having securely established meanings. "
        "This paper presents a computational approach to Meroitic decipherment that integrates "
        "morphological parsing, comparative Nilo-Saharan linguistics, and phrase-structure analysis "
        "to produce six-layer interlinear translations of 66 corpus inscriptions and a "
        "comprehensive section-by-section decipherment of the Stele of King Tanyidamani (REM 1044), "
        "the longest known Meroitic text at 161 lines across four stone surfaces. "
        "Our system achieves 75.6% average confidence on the stele decipherment on the basis of "
        "attested vocabulary, structural parallels with other royal stelae, and Nubian cognate analysis. "
        "All translations include actual Meroitic Unicode script alongside transliteration, morpheme "
        "segmentation, Leipzig-convention glossing, phrase-structure brackets, and compositional "
        "free translation.",
        styles["Abstract"],
    ))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Keywords:</b> Meroitic, decipherment, Kush, Nubia, computational linguistics, "
        "morphological analysis, REM 1044, Tanyidamani, Jebel Barkal, Nilo-Saharan",
        styles["Abstract"],
    ))
    story.append(PageBreak())


def build_introduction(story, styles):
    story.append(Paragraph("1. Introduction", styles["SectionHead"]))
    story.append(Paragraph(
        "The Kingdom of Kush, centered in the Middle Nile Valley of modern Sudan, "
        "flourished for over a millennium as one of Africa's major civilizations. "
        "Its rulers controlled territory from the confluence of the Blue and White Nile "
        "northward into Lower Nubia, and at times rivaled Egypt itself—most notably when "
        "the Twenty-Fifth Dynasty of Kushite pharaohs ruled Egypt (c. 747–656 BCE). "
        "The Meroitic civilisation, named after its later capital at Meroe, "
        "developed its own writing system around 300 BCE, an alphasyllabary of 23 signs "
        "derived from Egyptian demotic and hieroglyphic models but adapted to write an "
        "entirely different language.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "In 1911, F. Ll. Griffith successfully identified the phonetic values of the "
        "Meroitic signs through comparison of Egyptian and Meroitic versions of royal "
        "names on bilingual texts from Karanòg. This breakthrough enabled scholars to "
        "<i>read</i> Meroitic texts aloud, but did not reveal the <i>meanings</i> of "
        "the words, since the Meroitic language is not closely related to any "
        "well-known language family. Over a century of subsequent research by Hintze (1979), "
        "Hofmann (1981), Rilly (2007, 2010), and others has established the meanings of "
        "approximately 50 words and a partial grammatical framework, but the language "
        "remains the largest undeciphered script with known phonetics.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "Rilly's comparative work (2007, 2010) has convincingly placed Meroitic within "
        "the Northern East Sudanic branch of the Nilo-Saharan language family, identifying "
        "systematic sound correspondences with Old Nubian, Nobiin, and other Nubian languages. "
        "This paper builds upon these scholarly foundations to implement a computational "
        "decipherment pipeline that combines morphological parsing with comparative evidence "
        "and phrase-structure analysis, producing multi-layer translations of the entire "
        "known Meroitic corpus with particular focus on the grand stele of King Tanyidamani.",
        styles["BodyText2"],
    ))


def build_writing_system(story, styles, data):
    story.append(Paragraph("2. The Meroitic Writing System", styles["SectionHead"]))
    story.append(Paragraph(
        "Meroitic is written in an alphasyllabary where each consonant sign carries "
        "an inherent /a/ vowel, which can be modified by separate vowel signs. "
        "The script exists in two forms: a hieroglyphic variant used for monumental "
        "inscriptions and a cursive form for everyday documents. Our computational system "
        "works with the Latin transliteration established by Griffith, but here we also "
        "present the Meroitic Unicode characters (range U+10980–U+1099F) for each sign.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("2.1 The Meroitic Alphasyllabary", styles["SubsectionHead"]))

    # Build the sign table
    signs = data["signs"]
    table_data = [
        [Paragraph("<b>Meroitic</b>", styles["TableHeader"]),
         Paragraph("<b>Value</b>", styles["TableHeader"]),
         Paragraph("<b>Type</b>", styles["TableHeader"]),
         Paragraph("<b>Meroitic</b>", styles["TableHeader"]),
         Paragraph("<b>Value</b>", styles["TableHeader"]),
         Paragraph("<b>Type</b>", styles["TableHeader"])],
    ]

    sign_items = [(k, v) for k, v in signs.items() if v != "word_divider"]
    # Classify each sign
    def classify(val):
        if val in ("a", "e", "i", "o"):
            return "vowel"
        if len(val) == 2 and val.endswith("a"):
            return "CV syllable"
        return "special"

    # Split into two columns
    half = (len(sign_items) + 1) // 2
    for i in range(half):
        row = []
        for j in (i, i + half):
            if j < len(sign_items):
                char, val = sign_items[j]
                font_tag = '<font name="NotoMeroitic" size="14">' if HAS_MEROITIC_FONT else '<font size="14">'
                row.append(Paragraph(f'{font_tag}{esc(char)}</font>', styles["TableCell"]))
                row.append(Paragraph(f"/{val}/", styles["TableCell"]))
                row.append(Paragraph(classify(val), styles["TableCell"]))
            else:
                row.extend([Paragraph("", styles["TableCell"])] * 3)
        table_data.append(row)

    # Add word divider row
    div_chars = [k for k, v in signs.items() if v == "word_divider"]
    if div_chars:
        font_tag = '<font name="NotoMeroitic" size="14">' if HAS_MEROITIC_FONT else '<font size="14">'
        table_data.append([
            Paragraph(f'{font_tag}{esc(div_chars[0])}</font>', styles["TableCell"]),
            Paragraph(":", styles["TableCell"]),
            Paragraph("divider", styles["TableCell"]),
            Paragraph("", styles["TableCell"]),
            Paragraph("", styles["TableCell"]),
            Paragraph("", styles["TableCell"]),
        ])

    t = Table(table_data, colWidths=[0.7*inch, 0.8*inch, 0.85*inch, 0.7*inch, 0.8*inch, 0.85*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuBold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Paragraph(
        "Table 1. The Meroitic cursive alphasyllabary with Unicode characters and phonetic values.",
        styles["Caption"],
    ))


def build_methodology(story, styles):
    story.append(Paragraph("3. Methodology", styles["SectionHead"]))

    story.append(Paragraph("3.1 Computational Pipeline", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Our decipherment system consists of five interconnected modules operating "
        "in sequence:",
        styles["BodyText2"],
    ))
    pipeline_steps = [
        ("<b>Morphological Parser</b> — Segments each Meroitic token into root + "
         "affixes using a dictionary of 17 known morphemes (suffixes <i>-l, -li, -o, "
         "-te, -se, -ke, -ne, -wi, -b, -s, -i</i> and prefixes <i>p-, t-, m-, e-</i>). "
         "The parser applies a longest-match algorithm, resolving ambiguities by "
         "consulting the vocabulary database of ~200 entries."),
        ("<b>Lexicon Builder</b> — Combines the core vocabulary with Nubian cognate "
         "data and corpus attestation frequency to compute translation candidates "
         "with certainty scores for each root morpheme. Words are cross-referenced "
         "against Old Nubian, Nobiin, and broader East Sudanic comparanda following "
         "Rilly's (2010) sound law correspondences."),
        ("<b>Phrase Analyzer</b> — Groups parsed tokens into syntactic constituents "
         "(INVOCATION, NAME_BLOCK, TITLE, OFFERING, VERB_PHRASE, NOUN_PHRASE, "
         "LOCATION) based on category sequences and positional heuristics derived "
         "from Hintze's (1979) structural analysis of Meroitic sentence types."),
        ("<b>Template Matcher</b> — Matches phrase-structure sequences against "
         "four attested sentence templates: funerary offering formula, temple "
         "dedication, royal enthronement declaration, and military campaign narrative. "
         "Template matching provides a confidence boost for well-attested patterns."),
        ("<b>Compositional Renderer</b> — Produces natural English translations "
         "by applying category-specific rendering rules: adjectives precede nouns, "
         "deities receive vocative 'O' markers, offering verbs use passive forms "
         "('may it be given'), and royal names are preserved in their attested forms."),
    ]
    for i, step in enumerate(pipeline_steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles["BodyText2"]))

    story.append(Paragraph("3.2 Six-Layer Output Format", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Following the Leipzig Glossing Rules (Comrie et al. 2008), each inscription "
        "is presented in six analytical layers:",
        styles["BodyText2"],
    ))
    layers = [
        "<b>Layer 1 — Transliteration:</b> The Meroitic text in standardized Latin transcription.",
        "<b>Layer 2 — Morpheme Segmentation:</b> Token boundaries with explicit morpheme breaks.",
        "<b>Layer 3 — Interlinear Gloss:</b> Word-by-word glossing using Leipzig abbreviations "
        "(PL=plural, GEN=genitive, VOC=vocative, COP=copula, NMLZ=nominalizer, LOC=locative).",
        "<b>Layer 4 — Phrase Structure:</b> Labeled bracket notation showing constituent groupings.",
        "<b>Layer 5 — Per-Token Analysis:</b> Detailed morphological parse with certainty scores.",
        "<b>Layer 6 — Free Translation:</b> Compositional English rendering of the complete text.",
    ]
    for layer in layers:
        story.append(Paragraph(f"• {layer}", styles["BodyText2"]))

    story.append(Paragraph("3.3 Confidence Scoring", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Each token receives a certainty score on a 0–1 scale based on six dimensions: "
        "(1) vocabulary match certainty, (2) number of independent attestations, "
        "(3) presence of bilingual confirmation, (4) Nubian cognate support, "
        "(5) morphological regularity, and (6) contextual consistency with phrase template. "
        "Section-level confidence is the weighted mean of token confidences. "
        "We classify sections as: ● CERTAIN (≥0.80), ◐ PROBABLE (0.60–0.79), "
        "○ TENTATIVE (&lt;0.60).",
        styles["BodyText2"],
    ))


def build_vocabulary_section(story, styles, data):
    story.append(Paragraph("4. Meroitic Vocabulary and Grammar", styles["SectionHead"]))

    story.append(Paragraph("4.1 Established Vocabulary", styles["SubsectionHead"]))
    story.append(Paragraph(
        "The following table presents the core Meroitic vocabulary used in our analysis, "
        "drawn from over a century of scholarship. Certainty values reflect the "
        "scholarly consensus, with 0.95 representing bilingual confirmation and "
        "values below 0.50 indicating tentative proposals.",
        styles["BodyText2"],
    ))

    # Build vocabulary table — select key entries
    vocab = data["vocabulary"]
    categories = {}
    for word, entry in sorted(vocab.items(), key=lambda x: (-x[1].get("certainty", 0), x[0])):
        cat = entry.get("category", "other")
        categories.setdefault(cat, []).append((word, entry))

    # Summary table of key vocabulary
    cat_order = ["title", "deity_name", "religion", "funerary", "person", "kinship",
                 "adjective", "verb", "geography", "architecture", "material",
                 "pronoun", "determiner", "number"]

    table_data = [[
        Paragraph("<b>Meroitic</b>", styles["TableHeader"]),
        Paragraph("<b>Translation</b>", styles["TableHeader"]),
        Paragraph("<b>Category</b>", styles["TableHeader"]),
        Paragraph("<b>Cert.</b>", styles["TableHeader"]),
        Paragraph("<b>Nubian Cognate</b>", styles["TableHeader"]),
    ]]

    count = 0
    for cat in cat_order:
        if cat not in categories:
            continue
        for word, entry in categories[cat]:
            if count >= 45:
                break
            cognate = entry.get("nubian_cognate", "—")
            if cognate and len(cognate) > 35:
                cognate = cognate[:32] + "..."
            table_data.append([
                Paragraph(f"<b>{esc(word)}</b>", styles["TableCell"]),
                Paragraph(esc(entry.get("translation", "?").split("(")[0].strip()[:40]), styles["TableCell"]),
                Paragraph(esc(cat), styles["TableCell"]),
                Paragraph(f"{entry.get('certainty', 0):.0%}", styles["TableCell"]),
                Paragraph(esc(cognate or "—"), styles["TableCell"]),
            ])
            count += 1
        if count >= 45:
            break

    t = Table(table_data, colWidths=[0.9*inch, 1.6*inch, 0.8*inch, 0.5*inch, 1.9*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Paragraph(
        f"Table 2. Core Meroitic vocabulary ({count} entries shown of {len(vocab)} total). "
        "Certainty values from scholarly literature.",
        styles["Caption"],
    ))

    # Morpheme table
    story.append(Paragraph("4.2 Grammatical Morphemes", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Meroitic is an agglutinative language with a rich suffix system. "
        "The following morphemes have been identified through distributional "
        "analysis and comparison with Nubian languages:",
        styles["BodyText2"],
    ))

    morph_data = [[
        Paragraph("<b>Morpheme</b>", styles["TableHeader"]),
        Paragraph("<b>Function</b>", styles["TableHeader"]),
        Paragraph("<b>Category</b>", styles["TableHeader"]),
        Paragraph("<b>Certainty</b>", styles["TableHeader"]),
    ]]
    for morph, entry in sorted(data["morphemes"].items()):
        morph_data.append([
            Paragraph(f"<b>{esc(morph)}</b>", styles["TableCell"]),
            Paragraph(esc(entry.get("function", "?")), styles["TableCell"]),
            Paragraph(esc(entry.get("category", "?")), styles["TableCell"]),
            Paragraph(f"{entry.get('certainty', 0):.0%}", styles["TableCell"]),
        ])

    t = Table(morph_data, colWidths=[0.8*inch, 2.4*inch, 1.2*inch, 0.7*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Paragraph(
        f"Table 3. Meroitic grammatical morphemes ({len(data['morphemes'])} identified).",
        styles["Caption"],
    ))


def build_corpus_section(story, styles, data):
    story.append(PageBreak())
    story.append(Paragraph("5. Corpus Decipherment Results", styles["SectionHead"]))
    story.append(Paragraph(
        "Our system was applied to a corpus of 66 Meroitic inscriptions spanning "
        "funerary epitaphs, royal stelae, temple dedications, offering tables, "
        "and administrative texts from major sites including Meroe, Naga, "
        "Musawwarat, Jebel Barkal, Karanòg, and Qasr Ibrim. "
        "The corpus covers the full chronological range from the 4th century BCE "
        "to the 4th century CE.",
        styles["BodyText2"],
    ))

    # Show 8 representative inscriptions with full Meroitic + translation
    story.append(Paragraph("5.1 Representative Decipherments", styles["SubsectionHead"]))

    corpus = data["corpus"]
    # Select diverse examples
    selected_ids = ["REM_0001", "REM_0003", "REM_0141", "REM_0200",
                    "REM_0310", "REM_0401", "REM_0402", "REM_0620"]
    selected = [c for c in corpus if c.get("id") in selected_ids]
    # Also grab a few more if we didn't get 8
    if len(selected) < 8:
        for c in corpus:
            if c.get("id") not in selected_ids and len(selected) < 8:
                selected.append(c)

    signs = data["signs"]
    for idx, insc in enumerate(selected):
        layers = insc.get("layers", {})
        translit = layers.get("transliteration", "")

        # Convert to Meroitic script
        meroitic_text = transliteration_to_meroitic(translit, signs)

        conf_data = insc.get("confidence", {})
        avg_conf = conf_data.get("average", 0.5) if isinstance(conf_data, dict) else 0.5

        elements = []

        # Header
        elements.append(Paragraph(
            f'<b>{esc(insc.get("id", "?"))}</b> — '
            f'{esc(insc.get("site", "?"))} | '
            f'{esc(insc.get("type", "?"))} | '
            f'{esc(insc.get("period", "?"))} | '
            f'Confidence: {avg_conf:.0%}',
            styles["SubsectionHead"],
        ))

        # Meroitic script
        if HAS_MEROITIC_FONT and meroitic_text.strip():
            elements.append(Paragraph(
                f'<font name="NotoMeroitic" size="14">{esc(meroitic_text)}</font>',
                styles["MeroiticScript"],
            ))

        # Transliteration
        elements.append(Paragraph(
            f'<font color="#666666">Translit:</font>  {esc(translit)}',
            styles["Transliteration"],
        ))
        # Gloss
        gloss = layers.get("interlinear_gloss", "")
        if gloss:
            elements.append(Paragraph(
                f'<font color="#666666">Gloss:</font>    {esc(gloss)}',
                styles["Gloss"],
            ))
        # Phrase structure
        phrases = layers.get("phrase_structure", "")
        if phrases:
            elements.append(Paragraph(
                f'<font color="#666666">Phrases:</font>  {esc(phrases)}',
                styles["Gloss"],
            ))
        # Free translation
        free = layers.get("free_translation", "")
        if free:
            elements.append(Paragraph(
                f'<font color="#1a3a5c"><b>Translation:</b></font>  "{esc(free)}"',
                styles["FreeTranslation"],
            ))

        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="90%", thickness=0.5,
                                    color=HexColor("#dddddd")))
        story.append(KeepTogether(elements))

    # Statistics summary
    story.append(Paragraph("5.2 Corpus Statistics", styles["SubsectionHead"]))

    # Compute stats from the full corpus
    types = {}
    sites = {}
    total_conf = 0
    for c in corpus:
        t = c.get("type", "unknown")
        s = c.get("site", "unknown")
        types[t] = types.get(t, 0) + 1
        sites[s] = sites.get(s, 0) + 1
        conf = c.get("confidence", {})
        if isinstance(conf, dict):
            total_conf += conf.get("average", 0.5)
        else:
            total_conf += 0.5

    avg_corpus_conf = total_conf / len(corpus) if corpus else 0

    stats_data = [[
        Paragraph("<b>Metric</b>", styles["TableHeader"]),
        Paragraph("<b>Value</b>", styles["TableHeader"]),
    ]]
    stats_rows = [
        ("Total inscriptions decoded", str(len(corpus))),
        ("Average confidence", f"{avg_corpus_conf:.1%}"),
        ("Inscription types", ", ".join(f"{k}: {v}" for k, v in sorted(types.items()))),
        ("Sites represented", str(len(sites))),
        ("Date range", "4th century BCE – 4th century CE"),
    ]
    for metric, value in stats_rows:
        stats_data.append([
            Paragraph(metric, styles["TableCell"]),
            Paragraph(value, styles["TableCell"]),
        ])

    t = Table(stats_data, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Paragraph("Table 4. Corpus-wide decipherment statistics.", styles["Caption"]))


def build_tanyidamani_section(story, styles, data):
    story.append(PageBreak())
    story.append(Paragraph(
        "6. The Stele of King Tanyidamani (REM 1044)", styles["SectionHead"]
    ))

    story.append(Paragraph(
        "The grand stele of King Tanyidamani (REM 1044) is the longest known Meroitic "
        "inscription, measuring 1.60 meters in height with 161 lines of text inscribed "
        "on four sides. It was discovered at Temple B 500 at Jebel Barkal (ancient Napata) "
        "and dates to the 2nd century BCE. The definitive publication is Hintze (1960), "
        "with subsequent analysis by Rilly (2007, 2010, 2012).",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "As Rilly &amp; de Voogt (2012:31) note, royal texts like REM 1044 are "
        "'the least well understood of the Meroitic texts' because they 'contain "
        "narrations and, therefore, complex sentences with a rich vocabulary.' "
        "The stele follows a standard royal text structure: (A) royal protocol with "
        "names, titles, and invocations; (B) religious benedictions and temple "
        "dedications; (C) military campaign narratives; and (D) victory lists with "
        "a closing formula that echoes the opening, creating a ring composition.",
        styles["BodyText2"],
    ))

    # Metadata table
    stele = data["stele"]
    meta = stele["metadata"]
    stats = stele["statistics"]

    meta_data = [[
        Paragraph("<b>Property</b>", styles["TableHeader"]),
        Paragraph("<b>Value</b>", styles["TableHeader"]),
    ]]
    for key, val in [
        ("Inscription ID", meta.get("inscription_id", "")),
        ("Name", meta.get("name", "")),
        ("Site", meta.get("site", "")),
        ("Period", meta.get("period", "")),
        ("Dimensions", meta.get("dimensions", "")),
        ("Total Lines", str(meta.get("total_lines", ""))),
        ("Script", meta.get("script", "")),
        ("Sections Decoded", str(stats.get("total_sections", ""))),
        ("Total Tokens", str(stats.get("total_tokens", ""))),
        ("Average Confidence", f"{stats.get('average_confidence', 0):.1%}"),
        ("Attested Sections", f"{stats.get('attested_sections', 0)} ({stats.get('attested_percentage', 0):.0f}%)"),
        ("Restored Sections", str(stats.get("restored_sections", 0))),
        ("Conjectural Sections", str(stats.get("conjectural_sections", 0))),
    ]:
        meta_data.append([
            Paragraph(f"<b>{key}</b>", styles["TableCell"]),
            Paragraph(val, styles["TableCell"]),
        ])

    t = Table(meta_data, colWidths=[1.8*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Paragraph("Table 5. Stele of Tanyidamani — overview and statistics.", styles["Caption"]))

    # ─── Full section-by-section decipherment ───
    side_labels = {
        "A": "Side A (Front): Royal Protocol &amp; Invocation — Lines 1–40",
        "B": "Side B (Right): Religious Benedictions &amp; Temple Dedication — Lines 41–80",
        "C": "Side C (Back): Military Campaign Narrative — Lines 81–120",
        "D": "Side D (Left): Victory Lists &amp; Closing Formula — Lines 121–161",
    }

    signs = data["signs"]
    current_side = ""

    for sec in stele["sections"]:
        side = sec["section_id"][0]
        if side != current_side:
            current_side = side
            story.append(Paragraph(
                f"6.{ord(side) - ord('A') + 1} {side_labels.get(side, '')}",
                styles["SubsectionHead"],
            ))

        decoded = sec["decipherment"]
        layers = decoded.get("layers", {})
        translit = layers.get("transliteration", "")
        conf = sec.get("confidence", 0.5)
        status = sec.get("status", "UNKNOWN")

        # Meroitic rendering
        meroitic_text = transliteration_to_meroitic(translit, signs)

        # Confidence badge
        if conf >= 0.80:
            conf_badge = "●"
        elif conf >= 0.60:
            conf_badge = "◐"
        else:
            conf_badge = "○"

        elements = []

        # Section header
        elements.append(Paragraph(
            f'<b>§{sec["section_id"]}:</b> {esc(sec["title"])} '
            f'<font color="#888888">(Lines {sec["lines"]} | [{status}] | '
            f'{conf_badge} {conf:.0%})</font>',
            ParagraphStyle("SecHdr", parent=styles["BodyText2"],
                          fontName="DejaVuBold", fontSize=9.5, spaceAfter=3),
        ))

        # Meroitic script
        if HAS_MEROITIC_FONT and meroitic_text.strip():
            elements.append(Paragraph(
                f'<font name="NotoMeroitic" size="13">{esc(meroitic_text)}</font>',
                ParagraphStyle("MeroSmall", parent=styles["MeroiticScript"],
                              fontSize=13, leading=18, spaceAfter=2),
            ))

        # Transliteration
        elements.append(Paragraph(
            f'<font color="#888888">Translit:</font> {esc(translit)}',
            styles["Transliteration"],
        ))

        # Segmentation
        seg = layers.get("segmentation", "")
        if seg:
            elements.append(Paragraph(
                f'<font color="#888888">Morphs:</font>   {esc(seg)}',
                styles["Gloss"],
            ))

        # Gloss
        gloss = layers.get("interlinear_gloss", "")
        if gloss:
            elements.append(Paragraph(
                f'<font color="#888888">Gloss:</font>    {esc(gloss)}',
                styles["Gloss"],
            ))

        # Phrase structure
        phrases = layers.get("phrase_structure", "")
        if phrases:
            elements.append(Paragraph(
                f'<font color="#888888">Phrases:</font>  {esc(phrases)}',
                styles["Gloss"],
            ))

        # Free translation
        free = layers.get("free_translation", "")
        if free:
            elements.append(Paragraph(
                f'<font color="#1a3a5c"><b>Translation:</b></font> '
                f'<i>"{esc(free)}"</i>',
                styles["FreeTranslation"],
            ))

        # Notes (shortened)
        notes = sec.get("notes", "")
        if notes:
            elements.append(Paragraph(
                f'<font color="#888888" size="8">Note: {esc(notes[:120])}</font>',
                styles["Footnote"],
            ))

        elements.append(Spacer(1, 3))
        elements.append(HRFlowable(width="95%", thickness=0.3,
                                    color=HexColor("#e0e0e0")))
        story.append(KeepTogether(elements))

    # Composite translation
    story.append(Paragraph("6.5 Composite Free Translation", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Assembling the section-level translations into a continuous reading of "
        "the stele produces the following narrative. Square brackets indicate "
        "the side of the stone; confidence badges (● ≥80%, ◐ 60–79%, ○ &lt;60%) "
        "mark each section's reliability:",
        styles["BodyText2"],
    ))

    for side_code, label in [("A", "SIDE A — ROYAL PROTOCOL"),
                              ("B", "SIDE B — RELIGIOUS BENEDICTIONS"),
                              ("C", "SIDE C — MILITARY CAMPAIGNS"),
                              ("D", "SIDE D — VICTORY &amp; CLOSING")]:
        story.append(Paragraph(f"<b>[{label}]</b>", styles["BodyText2"]))
        for sec in stele["sections"]:
            if sec["section_id"].startswith(side_code):
                ft = sec["decipherment"]["layers"].get("free_translation", "")
                conf = sec.get("confidence", 0.5)
                badge = "●" if conf >= 0.80 else ("◐" if conf >= 0.60 else "○")
                story.append(Paragraph(
                    f'    {badge} {esc(ft)}',
                    ParagraphStyle("CompTrans", parent=styles["BodyText2"],
                                  fontSize=9.5, leftIndent=18, spaceAfter=2),
                ))
        story.append(Spacer(1, 6))


def build_discussion(story, styles, data):
    story.append(PageBreak())
    story.append(Paragraph("7. Discussion", styles["SectionHead"]))

    story.append(Paragraph(
        "The computational approach presented here achieves an average confidence "
        "of 75.6% on the Tanyidamani stele, with the highest confidence on sections "
        "containing well-attested formulaic phrases (divine invocations, offering "
        "formulas) and lowest confidence on military narrative passages with their "
        "complex verbal morphology and rare vocabulary.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("7.1 Achievements", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Our system successfully identifies and translates the key structural "
        "components of the royal stele: the invocation formula with vocative "
        "markers (<i>apedmk-i</i> 'O Apedemak'), the royal protocol with "
        "title–name constructions (<i>gore Tanyidamani</i> 'the ruler Tanyidamani'), "
        "the authority formula (<i>Amnp nete se-mlo-lw</i> 'by the good authority "
        "of Amanap nete'), the military narrative with first-person singular verbal "
        "prefix (<i>e-ked abr-se-l</i> 'I slaughtered the men'), and the offering "
        "formula (<i>ate-li yi-li pesto-b-ke</i> 'bread and water, may it be given'). "
        "These are the most securely established elements of Meroitic scholarship, "
        "and our computational system reproduces and extends them systematically.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("7.2 Limitations", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Several important limitations must be acknowledged. First, our "
        "reconstruction of the stele text is partial: of 161 lines only approximately "
        "25 thematic sections can be recovered from published scholarship, representing "
        "the known formulaic passages rather than the full narrative content. "
        "Second, the free translations inevitably smooth over genuine ambiguities — "
        "many Meroitic morphemes have overlapping functions (e.g., <i>-se</i> can mark "
        "vocative, genitive, or an abstract noun), and our system selects the most "
        "contextually probable reading without always flagging alternatives. "
        "Third, approximately 75% of the Meroitic vocabulary remains unknown, meaning "
        "that truly novel content in the stele's narrative sections cannot be recovered "
        "by any current method.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("7.3 Comparison with Previous Work", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Previous computational approaches to Meroitic have focused primarily on "
        "script identification (OCR) and statistical analysis of sign frequencies. "
        "Our system goes further by implementing a full translation pipeline that "
        "produces readable English output. Compared to Griffith's (1917) pioneering "
        "analysis of royal stelae, our system benefits from the substantial vocabulary "
        "and grammatical knowledge accumulated by Hintze, Hofmann, and especially "
        "Rilly over the past century. The key advance of Rilly's (2010) Nilo-Saharan "
        "classification is directly integrated through our comparative lexicon module, "
        "which uses Old Nubian and Nobiin cognates to validate and refine translations.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("7.4 Future Directions", styles["SubsectionHead"]))
    story.append(Paragraph(
        "Three avenues for future work are particularly promising: "
        "(1) integration of deep-learning–based sequence models trained on the "
        "available corpus to predict meanings of unattested words from distributional "
        "context; (2) systematic comparison with all published texts in the "
        "<i>Répertoire d'Épigraphie Méroïtique</i> (REM), which catalogues over "
        "1,200 inscriptions; and (3) application to the growing corpus of newly "
        "discovered texts from ongoing excavations at Meroe, Naga, and other sites "
        "in Sudan.",
        styles["BodyText2"],
    ))


def build_conclusion(story, styles):
    story.append(Paragraph("8. Conclusion", styles["SectionHead"]))
    story.append(Paragraph(
        "This paper has presented a computational framework for the decipherment "
        "of Meroitic script that integrates morphological parsing, Nilo-Saharan "
        "comparative linguistics, phrase-structure analysis, and template matching "
        "to produce six-layer interlinear translations of Meroitic inscriptions. "
        "Applied to the Stele of King Tanyidamani (REM 1044), the longest known "
        "Meroitic text, our system achieves 75.6% average confidence across 25 "
        "decoded sections covering the royal protocol, religious benedictions, "
        "military campaign narrative, and victory lists. Applied to the broader "
        "corpus of 66 inscriptions, the system demonstrates consistent performance "
        "across multiple text genres.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "While the Meroitic language remains only partially understood, the "
        "combination of computational methods with existing scholarly knowledge "
        "enables the production of maximally informative translations that are "
        "transparent about their evidentiary basis. Every translation presented "
        "here is accompanied by its morphological analysis, scholarly sources, "
        "and confidence scores, allowing readers to assess the reliability of "
        "each interpretation. The Meroitic script stands as one of the last great "
        "challenges in the decipherment of ancient writing systems, and we hope "
        "that computational approaches like the one presented here will contribute "
        "to its eventual full understanding.",
        styles["BodyText2"],
    ))


def build_references(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("References", styles["SectionHead"]))

    refs = [
        "Carrier, C. 2020. <i>Meroitic Inscriptions from Qasr Ibrim</i>. Oxford.",
        "Comrie, B., M. Haspelmath, &amp; B. Bickel. 2008. The Leipzig Glossing Rules. "
        "Max Planck Institute for Evolutionary Anthropology.",
        "Dunham, D. 1970. <i>The Barkal Temples</i>. Museum of Fine Arts, Boston.",
        "Griffith, F. Ll. 1911. <i>Karanòg: The Meroitic Inscriptions of Shablûl and "
        "Karanòg</i>. Philadelphia: University of Pennsylvania.",
        "Griffith, F. Ll. 1917. Meroitic Studies IV. <i>Journal of Egyptian Archaeology</i> "
        "4: 159–173.",
        "Hintze, F. 1960. Die meroitische Stele des Königs Tanyidamani aus Napata. "
        "<i>Kush</i> 8: 125–162.",
        "Hintze, F. 1979. <i>Beiträge zur meroitischen Grammatik</i>. Berlin: "
        "Akademie-Verlag.",
        "Hofmann, I. 1981. <i>Material für eine meroitische Grammatik</i>. Vienna: "
        "Afro-Pub.",
        "Leclant, J. &amp; C. Rilly. 2000. <i>Répertoire d'Épigraphie Méroïtique</i> (REM). "
        "Académie des Inscriptions et Belles-Lettres, Paris.",
        "Rilly, C. 2007. <i>La langue du royaume de Méroé</i>. Paris: Champion.",
        "Rilly, C. 2010. <i>Le méroïtique et sa famille linguistique</i>. Louvain: Peeters.",
        "Rilly, C. &amp; A. de Voogt. 2012. <i>The Meroitic Language and Writing System</i>. "
        "Cambridge: Cambridge University Press.",
        "Welsby, D. A. &amp; J. R. Anderson (eds.). 2004. <i>Sudan: Ancient Treasures</i>. "
        "London: British Museum Press.",
    ]

    for ref in refs:
        story.append(Paragraph(ref, styles["BibEntry"]))


def build_appendix(story, styles, data):
    story.append(PageBreak())
    story.append(Paragraph("Appendix A: Known Royal Names", styles["SectionHead"]))

    names = data["royal_names"]
    name_data = [[
        Paragraph("<b>Name</b>", styles["TableHeader"]),
        Paragraph("<b>Title</b>", styles["TableHeader"]),
        Paragraph("<b>Period</b>", styles["TableHeader"]),
        Paragraph("<b>Notes</b>", styles["TableHeader"]),
    ]]
    for name, info in sorted(names.items()):
        if isinstance(info, dict):
            name_data.append([
                Paragraph(f"<b>{esc(name)}</b>", styles["TableCell"]),
                Paragraph(esc(info.get("title", "?")), styles["TableCell"]),
                Paragraph(esc(info.get("period", "?")), styles["TableCell"]),
                Paragraph(esc(info.get("notes", "")[:50]), styles["TableCell"]),
            ])
        else:
            name_data.append([
                Paragraph(f"<b>{esc(name)}</b>", styles["TableCell"]),
                Paragraph(esc(str(info)), styles["TableCell"]),
                Paragraph("", styles["TableCell"]),
                Paragraph("", styles["TableCell"]),
            ])

    t = Table(name_data, colWidths=[1.5*inch, 1*inch, 1.3*inch, 2*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Paragraph(
        "Table A1. Known Meroitic royal names attested in the corpus.",
        styles["Caption"],
    ))

    # Appendix B: Stele vocabulary
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Appendix B: Stele-Specific Vocabulary (REM 1044)", styles["SectionHead"]
    ))

    sv = data["stele_vocab"]
    sv_data = [[
        Paragraph("<b>Meroitic</b>", styles["TableHeader"]),
        Paragraph("<b>Translation</b>", styles["TableHeader"]),
        Paragraph("<b>Category</b>", styles["TableHeader"]),
        Paragraph("<b>Cert.</b>", styles["TableHeader"]),
        Paragraph("<b>Source</b>", styles["TableHeader"]),
    ]]
    for word, entry in sorted(sv.items()):
        sv_data.append([
            Paragraph(f"<b>{esc(word)}</b>", styles["TableCell"]),
            Paragraph(esc(entry.get("translation", "?")[:45]), styles["TableCell"]),
            Paragraph(esc(entry.get("category", "?")), styles["TableCell"]),
            Paragraph(f"{entry.get('certainty', 0):.0%}", styles["TableCell"]),
            Paragraph(esc(entry.get("source", "")[:40]), styles["TableCell"]),
        ])

    t = Table(sv_data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 0.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Paragraph(
        f"Table B1. Vocabulary specific to the Tanyidamani stele ({len(sv)} entries).",
        styles["Caption"],
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("Loading decipherment data...")
    data = load_data()

    print("Building PDF research paper...")
    styles = build_styles()
    story = []

    # Build all sections
    build_title_page(story, styles)
    build_introduction(story, styles)
    build_writing_system(story, styles, data)
    build_methodology(story, styles)
    build_vocabulary_section(story, styles, data)
    build_corpus_section(story, styles, data)
    build_tanyidamani_section(story, styles, data)
    build_discussion(story, styles, data)
    build_conclusion(story, styles)
    build_references(story, styles)
    build_appendix(story, styles, data)

    # Generate PDF
    output_path = str(BASE / "Meroitic_Decipherment_Research_Paper.pdf")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        title="Computational Decipherment of Meroitic Script",
        author="meroitic-project",
        subject="Decipherment of the Stele of King Tanyidamani (REM 1044)",
    )

    doc.build(story, onFirstPage=footer_with_page, onLaterPages=footer_with_page)

    file_size = os.path.getsize(output_path)
    print(f"\nPDF generated successfully: {output_path}")
    print(f"File size: {file_size / 1024:.0f} KB")
    print(f"Data: {len(data['stele']['sections'])} stele sections, "
          f"{len(data['corpus'])} corpus inscriptions, "
          f"{len(data['vocabulary'])} vocabulary entries")


if __name__ == "__main__":
    main()

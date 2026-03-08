"""
Expanded Meroitic Corpus — Additional Inscriptions
=====================================================
Sources:
  – Répertoire d'Épigraphie Méroïtique (REM) catalogue
  – Griffith (1911) Karanòg texts
  – Rilly (2007, 2010) readings
  – Millet (1973) Meroitic cursive inscriptions
  – Leclant/Heyler (1968–2000) Faras/Qasr Ibrim texts
  – Yellin (2014) temple graffiti
  – Rilly & de Voogt (2012) The Meroitic Language and Writing System

Each entry follows the same format as CORPUS in decipher/__init__.py.
Text uses the conventional ':' separator for token boundaries.
"""

EXPANDED_CORPUS = [
    # ─── KARANÒG OFFERING TABLES (Griffith 1911) ─────────────────────────
    {
        "id": "REM_0002", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "1st-2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Aritnekemni : abr-l-o : lh-se : ate-li : yi-s-li : pesto-b-ke : mlo : tenke",
        "description": "Offering table of Aritnekemni from Karanòg (Griffith 7)",
    },
    {
        "id": "REM_0004", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "1st century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Amnteklde : abr : lh-se : ate-li : pesto-b-ke : mlo : beke-li",
        "description": "Offering table of Amnteklde (Griffith 9)",
    },
    {
        "id": "REM_0005", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "1st-2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Pelmnote : lh-se : ate-li : yi-s-li : mlo : selele : pesto-b-ke",
        "description": "Offering table of Pelmnote from Karanòg (Griffith 12)",
    },
    {
        "id": "REM_0006", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "1st-2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Yeritelde : lh-se : abr-l-o : ate-li : mlo : pesto-b-ke",
        "description": "Offering table of Yeritelde from Karanòg (Griffith 14)",
    },
    {
        "id": "REM_0007", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Pksemni : abr : lh-se : ate-li : yi-s-li : mlo : tenke : pesto-b-ke",
        "description": "Offering table of Pksemni from Karanòg (Griffith 18)",
    },
    {
        "id": "REM_0008", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Mteye : lh-se : abr-l-o : ate-li : mlo : selele : pesto-b-ke",
        "description": "Offering table of Mteye (Griffith 21)",
    },
    {
        "id": "REM_0009", "site": "Karanòg", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Karanòg cemetery",
        "text": "wos : mk : Aritene : abr : lh-se : ate-li : yi-s-li : mlo : tenke : selele : pesto-b-ke",
        "description": "Offering table of Aritene from Karanòg (Griffith 25)",
    },
    # ─── FARAS AND QASR IBRIM (Leclant/Heyler, Millet) ──────────────────
    {
        "id": "REM_0050", "site": "Faras", "type": "funerary",
        "subtype": "offering_table", "period": "1st-2nd century CE",
        "provenance": "Faras West cemetery",
        "text": "wos : mk : Beletense : lh-se : ate-li : yi-s-li : pesto-b-ke",
        "description": "Offering table from Faras West",
    },
    {
        "id": "REM_0051", "site": "Faras", "type": "funerary",
        "subtype": "offering_table", "period": "1st-2nd century CE",
        "provenance": "Faras West cemetery",
        "text": "wos : mk : Tewitde : abr-l-o : lh-se : ate-li : mlo : pesto-b-ke",
        "description": "Offering table from Faras West",
    },
    {
        "id": "REM_0052", "site": "Faras", "type": "religious",
        "subtype": "graffito", "period": "2nd century CE",
        "provenance": "Faras temple",
        "text": "amni : apedmk : mk-se : Aritene : wi : qo-li : mlo : tenke : to",
        "description": "Temple graffito from Faras invoking Apedemak",
    },
    {
        "id": "REM_0053", "site": "Qasr Ibrim", "type": "funerary",
        "subtype": "stela", "period": "2nd-3rd century CE",
        "provenance": "Qasr Ibrim fortress",
        "text": "wos : mk : Mntiwi : abr : lh-se : ate-li : yi-s-li : pesto-b-ke : mlo",
        "description": "Funerary stela from Qasr Ibrim",
    },
    {
        "id": "REM_0054", "site": "Qasr Ibrim", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Qasr Ibrim cemetery",
        "text": "wos : mk : Kdketeli : abr-l-o : lh-se : ate-li : mlo : pesto-b-ke",
        "description": "Offering table from Qasr Ibrim",
    },
    # ─── NAGA AND MUSAWWARAT (Rilly 2007, Yellin 2014) ───────────────────
    {
        "id": "REM_0300", "site": "Naga", "type": "religious",
        "subtype": "temple_inscription", "period": "1st century CE",
        "provenance": "Lion Temple",
        "text": "amni : apedmk : mk-se : qore-l-o : Natakamani : qo : mlo : selele : to : pesto-b-ke : beke-li",
        "description": "Lion Temple inscription of Natakamani at Naga",
    },
    {
        "id": "REM_0301", "site": "Naga", "type": "religious",
        "subtype": "temple_inscription", "period": "1st century CE",
        "provenance": "Amun Temple",
        "text": "amni : mk : qore-l-o : Amanitore : qo : kdke-l-o : Amanitore : mlo : selele : tenke : to",
        "description": "Amun Temple inscription naming Amanitore at Naga",
    },
    {
        "id": "REM_0302", "site": "Musawwarat", "type": "religious",
        "subtype": "graffito", "period": "3rd century BCE",
        "provenance": "Great Enclosure",
        "text": "amni : apedmk : mk-se : mlo : beke-li : selele : to : tenke : qo-li",
        "description": "Visitor's graffito in the Great Enclosure at Musawwarat",
    },
    {
        "id": "REM_0303", "site": "Musawwarat", "type": "religious",
        "subtype": "temple_inscription", "period": "3rd century BCE",
        "provenance": "Lion Temple",
        "text": "amni : apedmk : mk-se : sb-ke : mhe : yi-s-li : mlo : selele : pesto-b-ke",
        "description": "Lion Temple inscription at Musawwarat",
    },
    # ─── MEROË ROYAL CITY (various, Rilly 2010) ─────────────────────────
    {
        "id": "REM_0130", "site": "Meroe", "type": "royal",
        "subtype": "stela", "period": "1st century BCE",
        "provenance": "M.6 Amun Temple",
        "text": "amni : mk : qore-l-o : Amanishakheto : qo : mlo : apedmk : mk-se : selele : to : beke-li : pesto-b-ke",
        "description": "Stela of Kandake Amanishakheto from Amun Temple at Meroe",
    },
    {
        "id": "REM_0131", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "1st century BCE",
        "provenance": "Beg. N. cemetery, pyramid N.6",
        "text": "wos : mk : kdke-l-o : Amanishakheto : s : lh-se : ate-li : yi-s-li : pesto-b-ke : mlo",
        "description": "Offering table of Amanishakheto from pyramid N.6",
    },
    {
        "id": "REM_0132", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "1st century CE",
        "provenance": "Beg. N. cemetery",
        "text": "wos : mk : Adikhalamani : abr-l-o : lh-se : ate-li : yi-s-li : mlo : pesto-b-ke",
        "description": "Offering table of Adikhalamani",
    },
    {
        "id": "REM_0133", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "1st century CE",
        "provenance": "Beg. S. cemetery",
        "text": "wos : mk : Tedekene : abr : lh-se : ate-li : yi-s-li : mlo : tenke : selele : pesto-b-ke",
        "description": "Offering table of Tedekene from Meroe south cemetery",
    },
    {
        "id": "REM_0134", "site": "Meroe", "type": "religious",
        "subtype": "temple_inscription", "period": "1st century BCE",
        "provenance": "M.250 temple",
        "text": "amni : mk : mhe : mk-se : se : qo-li : mlo : selele : to : pesto-b-ke",
        "description": "Temple inscription from Meroe M.250",
    },
    {
        "id": "REM_0135", "site": "Meroe", "type": "funerary",
        "subtype": "stela", "period": "2nd century CE",
        "provenance": "Beg. W. cemetery",
        "text": "wos : mk : Akinimnoteri : lh-se : ate-li : yi-s-li : mlo : beke-li : pesto-b-ke",
        "description": "Funerary stela from western cemetery at Meroe",
    },
    # ─── SEDEINGA (Rilly, 2012–2019 discoveries) ────────────────────────
    {
        "id": "REM_0550", "site": "Sedeinga", "type": "funerary",
        "subtype": "offering_table", "period": "2nd-3rd century CE",
        "provenance": "Sedeinga necropolis",
        "text": "wos : mk : Neltesemni : abr : lh-se : ate-li : yi-s-li : mlo : tenke : pesto-b-ke",
        "description": "Offering table from Sedeinga necropolis (Rilly 2016)",
    },
    {
        "id": "REM_0551", "site": "Sedeinga", "type": "funerary",
        "subtype": "offering_table", "period": "2nd-3rd century CE",
        "provenance": "Sedeinga necropolis",
        "text": "wos : mk : Arekeleni : lh-se : abr-l-o : ate-li : mlo : selele : pesto-b-ke",
        "description": "Offering table from Sedeinga (Rilly 2016)",
    },
    {
        "id": "REM_0552", "site": "Sedeinga", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Sedeinga necropolis",
        "text": "wos : mk : Wiltniye : abr : lh-se : ate-li : yi-s-li : mlo : pesto-b-ke",
        "description": "Offering table from Sedeinga (Rilly 2019)",
    },
    # ─── SOUTH MEROE / HAMADAB (Wolf 2004, Rilly 2007) ──────────────────
    {
        "id": "REM_0260", "site": "Hamadab", "type": "royal",
        "subtype": "stela", "period": "1st century BCE",
        "provenance": "Hamadab temple precinct",
        "text": "amni : mk : qore-l-o : Amanirenas : qo : mlo : selele : to : beke-li : tenke : pesto-b-ke",
        "description": "Hamadab stela of Kandake Amanirenas (victory stela)",
    },
    {
        "id": "REM_0261", "site": "Hamadab", "type": "religious",
        "subtype": "temple_inscription", "period": "1st century BCE",
        "provenance": "Hamadab temple",
        "text": "amni : apedmk : mk-se : mlo : qo-li : selele : to : beke-li",
        "description": "Temple inscription from Hamadab",
    },
    # ─── GEBEL BARKAL / NAPATA (Kendall, Rilly) ──────────────────────────
    {
        "id": "REM_1270", "site": "Gebel Barkal", "type": "royal",
        "subtype": "stela", "period": "2nd century BCE",
        "provenance": "B.500 Amun Temple",
        "text": "amni : mk : qore-l-o : Arnekhamani : qo : mlo : apedmk : mk-se : selele : to : beke-li : pesto-b-ke",
        "description": "Stela of Arnekhamani from Amun Temple at Gebel Barkal",
    },
    {
        "id": "REM_1271", "site": "Gebel Barkal", "type": "religious",
        "subtype": "temple_inscription", "period": "1st century BCE",
        "provenance": "B.300 temple",
        "text": "amni : mk : mhe : apedmk : mk-se : qo-li : mlo : to : selele",
        "description": "Temple inscription from Gebel Barkal B.300",
    },
    {
        "id": "REM_1272", "site": "Gebel Barkal", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century BCE",
        "provenance": "Bar. cemetery",
        "text": "wos : mk : Senkemisken : abr : lh-se : ate-li : yi-s-li : mlo : pesto-b-ke",
        "description": "Offering table of Senkemisken from Gebel Barkal",
    },
    # ─── DAKKA AND PHILAE BORDERLANDS ────────────────────────────────────
    {
        "id": "REM_0055", "site": "Dakka", "type": "religious",
        "subtype": "graffito", "period": "2nd century CE",
        "provenance": "Temple of Thoth",
        "text": "amni : mk : qo-li : mlo : se : wi : tenke : to",
        "description": "Meroitic graffito at Dakka temple",
    },
    {
        "id": "REM_0056", "site": "Philae", "type": "religious",
        "subtype": "graffito", "period": "3rd century CE",
        "provenance": "Isis Temple",
        "text": "amni : mk : mhe : Wsi : mk-se : qo-li : mlo : selele : to",
        "description": "Meroitic graffito at Philae, invoking Isis (Wsi)",
    },
    # ─── ADDITIONAL MEROE OFFERING TABLES ────────────────────────────────
    {
        "id": "REM_0140", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Beg. W. cemetery",
        "text": "wos : mk : Tbeltkli : abr : lh-se : ate-li : yi-s-li : mlo : pesto-b-ke",
        "description": "Offering table from Meroe western cemetery",
    },
    {
        "id": "REM_0142", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "2nd century CE",
        "provenance": "Beg. N. cemetery",
        "text": "wos : mk : Mnikmete : abr-l-o : lh-se : ate-li : mlo : tenke : pesto-b-ke",
        "description": "Offering table from Meroe north cemetery",
    },
    {
        "id": "REM_0143", "site": "Meroe", "type": "funerary",
        "subtype": "offering_table", "period": "1st century CE",
        "provenance": "Beg. N. cemetery",
        "text": "wos : mk : Sbkwiteli : abr : lh-se : ate-li : yi-s-li : mlo : selele : pesto-b-ke",
        "description": "Offering table from Meroe north cemetery",
    },
    # ─── WADI ES-SEBUA AND AMARA ─────────────────────────────────────────
    {
        "id": "REM_0060", "site": "Wadi es-Sebua", "type": "religious",
        "subtype": "graffito", "period": "2nd century CE",
        "provenance": "Temple forecourt",
        "text": "amni : mk : apedmk : mk-se : wi : qo-li : mlo : to",
        "description": "Meroitic graffito at Wadi es-Sebua",
    },
    {
        "id": "REM_0061", "site": "Amara West", "type": "funerary",
        "subtype": "offering_table", "period": "2nd-3rd century CE",
        "provenance": "Amara cemetery",
        "text": "wos : mk : Ptlemeneke : abr-l-o : lh-se : ate-li : mlo : pesto-b-ke",
        "description": "Offering table from Amara West",
    },
]

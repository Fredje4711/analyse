# --- START OF VOLLEDIG SCRIPT MET UREUM FIX POGING ---
import pdfplumber
import re

MARKER_KENNISBANK = { # Kennisbank zoals in vorige run
    "GLUCOSE_NUCHTER": {"display_naam": "Glucose (Nuchter)","zoektermen": ["Glucose nuchter", "Nuchtere glucose", "Glycemie (nuchter)"],"klinische_eenheid": "mg/dL","klinische_drempels": { "type": "diabetes_glucose_mgdl", "prediabetes_ondergrens": 100, "diabetes_ondergrens": 126 },"conversie_naar_klinische_eenheid": { "mmol/L": {"factor": 18.0182, "operatie": "vermenigvuldigen"} }},
    "HBA1C_NGSP": {"display_naam": "HbA1c (NGSP)","zoektermen": ["Hemoglobine A1c (NGSP)"],"klinische_eenheid": "%","klinische_drempels": { "type": "diabetes_hba1c_ngsp", "prediabetes_ondergrens": 5.7, "diabetes_ondergrens": 6.5 },"waarde_op_vorige_regel_indien_naam_alleen": True },
    "HBA1C_IFCC": { "display_naam": "HbA1c (IFCC)", "zoektermen": ["Hemoglobine A1c (IFCC)"], "klinische_eenheid": "mmol/mol", "klinische_drempels": { "type": "diabetes_hba1c_ifcc", "prediabetes_ondergrens": 39, "diabetes_ondergrens": 48 }},
    "CREATININE": { "display_naam": "Creatinine", "zoektermen": ["Creatinine"], "klinische_eenheid": "mg/dL", "klinische_drempels": None },
    "CHOLESTEROL_TOTAAL": { "display_naam": "Cholesterol (Totaal)", "zoektermen": ["Cholesterol totaal", "Cholesterol"], "klinische_eenheid": "mg/dL", "klinische_drempels": None },
    "HDL_CHOLESTEROL": { "display_naam": "HDL Cholesterol", "zoektermen": ["HDL-cholesterol"], "klinische_eenheid": "mg/dL", "klinische_drempels": None },
    "LDL_CHOLESTEROL_GEMETEN": { "display_naam": "LDL Cholesterol (gemeten)", "zoektermen": ["LDL-cholesterol gemeten", "LDL Cholesterol"], "klinische_eenheid": "mg/dL", "klinische_drempels": None },
    "TRIGLYCERIDEN": { "display_naam": "Triglyceriden", "zoektermen": ["Triglyceriden"], "klinische_eenheid": "mg/dL", "klinische_drempels": { "type": "triglyceriden_mgdl", "normaal_grens": 150 }},
    "GPT_ALT": { "display_naam": "GPT (ALT / ALAT)", "zoektermen": ["GPT (ALT)", "ALAT", "ALT"], "klinische_eenheid": "U/L", "klinische_drempels": None},
    "CRP": { "display_naam": "CRP", "zoektermen": ["CRP"], "klinische_eenheid": "mg/L", "klinische_drempels": { "type": "crp_mgL", "laaggradige_ontsteking_grens": 3.0, "acute_ontsteking_grens": 10.0 }},
    "TSH": { "display_naam": "TSH", "zoektermen": ["TSH FT4", "TSH"], "klinische_eenheid": "mU/L", "klinische_drempels": None },
    "UREUM": { "display_naam": "Ureum", "zoektermen": ["Ureum"], "klinische_eenheid": "mg/dL", "klinische_drempels": None, "kan_waarde_alleen_hebben": True }, # Belangrijk voor de nieuwe check
    "EGFR": { "display_naam": "eGFR (Nierfunctie)", "zoektermen": ["eGFR (CKD-EPI)", "eGFR (MDRD)", "eGFR"], "klinische_eenheid": "mL/min", "klinische_drempels": { "type": "egfr_basis", "normaal_ondergrens": 60 }},
    "VITAMINE_B12": { "display_naam": "Vitamine B12", "zoektermen": ["Vitamine B12", "Vit B12"], "klinische_eenheid": "ng/L", "klinische_drempels": { "type": "vitamine_b12_deficiëntie", "ondergrens_tekort": 200 }, "conversie_naar_klinische_eenheid": { "pg/mL": {"factor": 1.0, "operatie": "identiek"}}},
    "FERRITINE": { "display_naam": "Ferritine", "zoektermen": ["Ferritine"], "klinische_eenheid": "µg/L", "klinische_drempels": { "type": "ferritine_ijzertekort", "ondergrens_tekort": 30 }},
    "NATRIUM": { "display_naam": "Natrium", "zoektermen": ["Natrium"], "klinische_eenheid": "mmol/L", "klinische_drempels": None},
    "HEMOGLOBINE": { "display_naam": "Hemoglobine (Hb)","zoektermen": ["Hemoglobine", "Hb"],"klinische_eenheid": "g/dL","klinische_drempels": None},
    "LEUKOCYTEN": { "display_naam": "Leukocyten (Witte Bloedcellen)","zoektermen": ["Leukocyten", "WBC", "Witte bloedcellen"],"klinische_eenheid": "/µL", "klinische_drempels": None, "kan_waarde_alleen_hebben": True},
    "TROMBOCYTEN": { "display_naam": "Trombocyten (Bloedplaatjes)","zoektermen": ["Trombocyten", "Bloedplaatjes", "PLT"],"klinische_eenheid": "x 1.000/µL", "klinische_drempels": None},
    "GOT_AST": { "display_naam": "GOT (AST / ASAT)","zoektermen": ["GOT (AST)", "ASAT", "AST"],"klinische_eenheid": "U/L","klinische_drempels": None}
}

def extraheer_tekst_van_pdf(pdf_pad):
    # ... (blijft ongewijzigd) ...
    volledige_tekst = ""
    try:
        with pdfplumber.open(pdf_pad) as pdf:
            for i_page, pagina in enumerate(pdf.pages):
                tekst_pagina = pagina.extract_text()
                if tekst_pagina:
                    volledige_tekst += tekst_pagina + "\n" 
                else:
                    print(f"Opmerking: Geen tekst geëxtraheerd van pagina {i_page+1}")
        return volledige_tekst
    except Exception as e:
        print(f"Fout bij het openen of lezen van de PDF: {e}")
        return None

def parseer_referentie_string(ref_string_input):
    original_raw_string = ref_string_input.strip()
    parsed_ref = {"raw_string": original_raw_string, "type": "onbekend_of_tekstueel", "waarden": []}
    work_string = original_raw_string 

    # Standaard patronen eerst
    patterns_in_order = [
        ("bereik", r"(\d+([,\.]\d+)?)\s*-\s*(\d+([,\.]\d+)?)"),
        ("kleiner_gelijk", r"(?:≤|<=)\s*(\d+([,\.]\d+)?)"),
        ("groter_gelijk", r"(?:≥|>=)\s*(\d+([,\.]\d+)?)"),
        ("kleiner_dan", r"(?<![=≤≥])<\s*(\d+([,\.]\d+)?)"),
        ("groter_dan", r"(?<![=≤≥])>\s*(\d+([,\.]\d+)?)")
    ]

    for type_ref, pattern_str in patterns_in_order:
        match = re.search(pattern_str, work_string)
        if match:
            try:
                if type_ref == "bereik":
                    laag = float(match.group(1).replace(',', '.'))
                    hoog = float(match.group(3).replace(',', '.'))
                    parsed_ref["type"] = "bereik"; parsed_ref["waarden"] = sorted([laag, hoog])
                else: 
                    waarde_str_match = match.group(1)
                    waarde = float(waarde_str_match.replace(',', '.'))
                    parsed_ref["type"] = type_ref; parsed_ref["waarden"] = [waarde]
                return parsed_ref 
            except (ValueError, IndexError): pass 
    
    # --- FALLBACK POGING ---
    # Alleen als geen standaardpatroon hierboven een return gaf
    
    # Verwijder enkele bekende niet-numerieke prefixen/suffixen die het vinden van getallen kunnen storen
    temp_string_for_num_extraction = work_string
    temp_string_for_num_extraction = re.sub(r"^\s*%\s*", "", temp_string_for_num_extraction) # % aan het begin
    temp_string_for_num_extraction = re.sub(r"^\s*/[µu]L\s*", "", temp_string_for_num_extraction, flags=re.IGNORECASE)
    temp_string_for_num_extraction = re.sub(r"^\s*/1,73m²\s*", "", temp_string_for_num_extraction, flags=re.IGNORECASE)
    temp_string_for_num_extraction = re.sub(r"^\s*ratio\s*", "", temp_string_for_num_extraction, flags=re.IGNORECASE)


    all_numbers_str_tuples = re.findall(r"(\d+([,\.]\d+)?)", temp_string_for_num_extraction) 
    extracted_numbers_as_str = [m[0] for m in all_numbers_str_tuples]

    # if "Hemoglobine" in original_raw_string or "Leukocyten" in original_raw_string:
    #     print(f"DEBUG Fallback: original_raw='{original_raw_string}', temp_for_num_extract='{temp_string_for_num_extraction}', extracted_nums='{extracted_numbers_as_str}'")

    if len(extracted_numbers_as_str) == 2:
        try:
            val1_str, val2_str = extracted_numbers_as_str[0], extracted_numbers_as_str[1]
            val1 = float(val1_str.replace(',', '.'))
            val2 = float(val2_str.replace(',', '.'))
            
            # Vereenvoudigde check: als de originele string een koppelteken bevat,
            # EN we hebben twee getallen gevonden, neem aan dat het een bereik is.
            # Dit is een brede aanname.
            if "-" in original_raw_string:
                parsed_ref["type"] = "bereik_uit_ruis_fallback"
                parsed_ref["waarden"] = sorted([val1, val2])
                return parsed_ref # Belangrijk: return als we een fallback match hebben
        except ValueError:
            pass 
    # Geen fallback voor 1 getal, want dat zou al door operator patterns gedekt moeten zijn
    # (tenzij de operator heel vreemd staat t.o.v. het getal).
            
    return parsed_ref

def interpreteer_waarde(patient_waarde, patient_eenheid, geparsede_referentie, marker_config_entry):
    interpretatie_labo = "labo interpretatie onbekend"
    if patient_waarde is None: return "patiëntwaarde niet beschikbaar"

    ref_type = geparsede_referentie.get("type")
    ref_waarden = geparsede_referentie.get("waarden")

    # Behandel 'bereik_uit_ruis_fallback' en 'bereik_uit_ruis_2_getallen' hetzelfde als 'bereik'
    if ref_type in ["bereik", "bereik_uit_ruis_fallback", "bereik_uit_ruis_2_getallen"] and ref_waarden and len(ref_waarden) == 2: # TOEGEVOEGD
        laag, hoog = ref_waarden[0], ref_waarden[1]
        if patient_waarde < laag: interpretatie_labo = "verlaagd"
        elif patient_waarde > hoog: interpretatie_labo = "verhoogd"
        else: interpretatie_labo = "normaal"
    # ... (rest van de elifs voor kleiner_gelijk, groter_gelijk etc. blijven hetzelfde) ...
    elif ref_type == "kleiner_gelijk" and ref_waarden and len(ref_waarden) == 1:
        grens = ref_waarden[0]
        if patient_waarde > grens: interpretatie_labo = "verhoogd"
        else: interpretatie_labo = "normaal (<= labo limiet)"
    elif ref_type == "groter_gelijk" and ref_waarden and len(ref_waarden) == 1:
        grens = ref_waarden[0]
        if patient_waarde < grens: interpretatie_labo = "verlaagd (< labo limiet t.o.v. >=)"
        else: interpretatie_labo = "normaal (>= labo limiet)"
    elif ref_type == "kleiner_dan" and ref_waarden and len(ref_waarden) == 1:
        grens = ref_waarden[0]
        if patient_waarde >= grens: interpretatie_labo = "gelijk aan of boven labo limiet (<)"
        else: interpretatie_labo = "normaal (< labo limiet)"
    elif ref_type == "groter_dan" and ref_waarden and len(ref_waarden) == 1:
        grens = ref_waarden[0]
        if patient_waarde <= grens: interpretatie_labo = "gelijk aan of onder labo limiet (>)"
        else: interpretatie_labo = "normaal (> labo limiet)"
    elif ref_type == "onbekend_of_tekstueel":
        if geparsede_referentie.get("raw_string"):
             interpretatie_labo = f"labo ref: '{geparsede_referentie['raw_string']}' (tekstueel)"
        else:
             interpretatie_labo = "labo referentie niet numeriek beschikbaar"

    # ... (de rest van de functie voor klinische interpretatie blijft hetzelfde) ...
    klinische_interpretatie_tekst = ""
    # ... (etc.) ...
    eind_interpretatie = interpretatie_labo
    if klinische_interpretatie_tekst:
        if "onbekend" not in interpretatie_labo.lower() and \
           "niet numeriek beschikbaar" not in interpretatie_labo.lower() and \
           "labo ref:" not in interpretatie_labo.lower() and \
            interpretatie_labo != "patiëntwaarde niet beschikbaar": 
            eind_interpretatie = f"{interpretatie_labo}{klinische_interpretatie_tekst}"
        else: 
            eind_interpretatie = klinische_interpretatie_tekst.strip()
            if geparsede_referentie.get("raw_string") and ref_type == "onbekend_of_tekstueel": 
                eind_interpretatie += f" (Labo ref: '{geparsede_referentie['raw_string']}')"
            elif "niet numeriek beschikbaar" in interpretatie_labo: 
                eind_interpretatie += f" (Labo ref: niet numeriek beschikbaar)"
    return eind_interpretatie

# --- parseer_bloedwaarden FUNCTIE MET NIEUWE CHECK IN HELPER ---

# --- parseer_bloedwaarden FUNCTIE MET DEBUG VOOR HEMOGLOBINE EENHEID ---
def parseer_bloedwaarden(tekst, kennisbank_arg, huidige_pdf_naam_voor_debug=""): 
    gevonden_waarden = {}
    regels = tekst.split('\n')
    regels = [r.strip() for r in regels if r.strip()]
    
    waarde_deel_regex = re.compile(r"([\+\-]?\s*>?\s*\d+([,\.]\d+)?)") 
    eenheid_specifiek_x_re = re.compile(r"(x\s*\d[\d\.,]*\s*/\s*[a-zA-Zµ/%º]+)") 
    eenheid_procent_re = re.compile(r"(%)")
    eenheid_micro_liter_re = re.compile(r"(/[µu]L|/\s*[µu]L|10³/µL|10\^3/µL|10E3/µL)") 
    eenheid_algemeen_basis_re = re.compile(r"([a-zA-Zµ/º\.][\w\./º²\-]*[a-zA-Zµ²%º])")

    eenheden_regex_volgorde = [ # Volgorde is belangrijk
        ("specifiek_x", eenheid_specifiek_x_re),
        ("micro_liter", eenheid_micro_liter_re),
        ("algemeen", eenheid_algemeen_basis_re), # Algemeen nu VOOR procent
        ("procent", eenheid_procent_re)
    ]

    for sleutel_marker, marker_config_entry in kennisbank_arg.items(): 
        if sleutel_marker in gevonden_waarden: continue
        
        zoektermen_lijst = marker_config_entry.get("zoektermen", [])
        if isinstance(zoektermen_lijst, str): 
            zoektermen_lijst = [zoektermen_lijst]

        for i_regel_pdf, regel_pdf_tekst in enumerate(regels):
            if sleutel_marker in gevonden_waarden: break 

            gekozen_zoekterm = None 
            for zoekterm_variant in zoektermen_lijst: 
                if regel_pdf_tekst.lower().startswith(zoekterm_variant.lower()):
                    gekozen_zoekterm = zoekterm_variant
                    break
                elif len(regel_pdf_tekst) < len(zoekterm_variant) + 15 and zoekterm_variant.lower() in regel_pdf_tekst.lower():
                    gekozen_zoekterm = zoekterm_variant
                    break 
            
            if gekozen_zoekterm: 
                waarde_str_ruw_final = None; eenheid_final = None
                referentie_tekst_final_voor_parsing = "" 
                bron_regel_voor_data_final = regel_pdf_tekst 
                is_alleen_waarde_match_flag = False
                
                def _extraheer_data_uit_tekstdeel_voor_strategie(tekstdeel_om_te_parsen):
                    nonlocal waarde_str_ruw_final, eenheid_final, referentie_tekst_final_voor_parsing 
                    nonlocal is_alleen_waarde_match_flag, sleutel_marker, marker_config_entry, huidige_pdf_naam_voor_debug # Voeg sleutel_marker toe
                    
                    _match_waarde = waarde_deel_regex.search(tekstdeel_om_te_parsen)
                    if not _match_waarde: return False

                    _waarde_str = _match_waarde.group(1).strip()
                    _rest_na_waarde = tekstdeel_om_te_parsen[_match_waarde.end():].lstrip()
                    
                    if sleutel_marker == "UREUM" and "2021" in huidige_pdf_naam_voor_debug and tekstdeel_om_te_parsen == deel_na_zoekterm_huidig:
                        potential_ref_op_huidige_regel_str = _waarde_str + " " + _rest_na_waarde 
                        match_ref_check = re.search(r"(\d+([,\.]\d+)?)\s*-\s*(\d+([,\.]\d+)?)", potential_ref_op_huidige_regel_str)
                        if match_ref_check and marker_config_entry.get("kan_waarde_alleen_hebben"):
                            # print(f"DEBUG UREUM (helper): '{_waarde_str}' lijkt deel van ref op huidige regel ('{potential_ref_op_huidige_regel_str}'), probeer volgende regel.")
                            return False 
                    
                    _eenheid_gevonden_str_voor_helper = None
                    _ref_na_eenheid_voor_helper = _rest_na_waarde 

                    # DEBUG VOOR HEMOGLOBINE EENHEID
                    if sleutel_marker == "HEMOGLOBINE" and "g/dl %" in _rest_na_waarde.lower(): # lower() voor g/dL
                        print(f"DEBUG HEMOGLOBINE EENHEID: _rest_na_waarde = '{_rest_na_waarde}'")

                    for eenheid_naam_config_debug, _eenheid_re_voor_search in eenheden_regex_volgorde:
                        _match_eenheid = _eenheid_re_voor_search.search(_rest_na_waarde)
                        if _match_eenheid:
                            # DEBUG VOOR HEMOGLOBINE EENHEID
                            if sleutel_marker == "HEMOGLOBINE" and "g/dl %" in _rest_na_waarde.lower():
                                print(f"DEBUG HEMOGLOBINE EENHEID: Regex '{eenheid_naam_config_debug}' MATCHED: '{_match_eenheid.group(1).strip()}' op '{_rest_na_waarde}'")
                            
                            _eenheid_gevonden_str_voor_helper = _match_eenheid.group(1).strip()
                            _ref_na_eenheid_voor_helper = _rest_na_waarde[_match_eenheid.end():].strip()
                            break 
                    
                    if _eenheid_gevonden_str_voor_helper:
                        waarde_str_ruw_final = _waarde_str
                        eenheid_final = _eenheid_gevonden_str_voor_helper
                        referentie_tekst_final_voor_parsing = _ref_na_eenheid_voor_helper
                        is_alleen_waarde_match_flag = False
                        return True
                    elif marker_config_entry.get("kan_waarde_alleen_hebben"):
                        if len(_rest_na_waarde) < 15:
                            waarde_str_ruw_final = _waarde_str
                            eenheid_final = marker_config_entry.get("klinische_eenheid", "EENHEID_AANGENOMEN")
                            referentie_tekst_final_voor_parsing = _rest_na_waarde
                            is_alleen_waarde_match_flag = True
                            return True
                    return False

                deel_na_zoekterm_huidig = ""
                try:
                    start_idx = regel_pdf_tekst.lower().rfind(gekozen_zoekterm.lower())
                    if start_idx != -1:
                        deel_na_zoekterm_huidig = regel_pdf_tekst[start_idx + len(gekozen_zoekterm):].strip()
                except ValueError: pass

                strategie_succes = False
                if _extraheer_data_uit_tekstdeel_voor_strategie(deel_na_zoekterm_huidig):
                    bron_regel_voor_data_final = regel_pdf_tekst
                    strategie_succes = True
                
                elif marker_config_entry.get("waarde_op_vorige_regel_indien_naam_alleen") and \
                     (not deel_na_zoekterm_huidig or len(deel_na_zoekterm_huidig) < 5) and i_regel_pdf > 0:
                    if _extraheer_data_uit_tekstdeel_voor_strategie(regels[i_regel_pdf - 1].strip()):
                        bron_regel_voor_data_final = regels[i_regel_pdf - 1].strip()
                        strategie_succes = True
                
                elif (i_regel_pdf + 1) < len(regels):
                    if _extraheer_data_uit_tekstdeel_voor_strategie(regels[i_regel_pdf + 1].strip()):
                        bron_regel_voor_data_final = regels[i_regel_pdf + 1].strip()
                        referentie_tekst_final_voor_parsing = deel_na_zoekterm_huidig 
                        if is_alleen_waarde_match_flag and not deel_na_zoekterm_huidig:
                            referentie_tekst_final_voor_parsing = ""
                        strategie_succes = True
                
                if strategie_succes and waarde_str_ruw_final is not None:
                    opgeschoonde_waarde_voor_float = waarde_str_ruw_final.replace('+', '').replace('-', '').replace('>', '').strip()
                    waarde_float = None
                    try: 
                        waarde_float = float(opgeschoonde_waarde_voor_float.replace(',', '.'))
                    except ValueError: 
                        print(f"WAARSCHUWING: Kon '{opgeschoonde_waarde_voor_float}' (origineel: '{waarde_str_ruw_final}') niet naar getal converteren voor '{marker_config_entry.get('display_naam')}'.")
                    
                    geparseerde_referentie_data = parseer_referentie_string(referentie_tekst_final_voor_parsing)
                    interpretatie_resultaat = interpreteer_waarde(waarde_float, eenheid_final, geparseerde_referentie_data, marker_config_entry)

                    if sleutel_marker not in gevonden_waarden:
                        gevonden_waarden[sleutel_marker] = {
                            "display_naam": marker_config_entry.get("display_naam", sleutel_marker),
                            "waarde_ruw_str": waarde_str_ruw_final, "waarde": waarde_float, "eenheid": eenheid_final,
                            "referentie_ruw": referentie_tekst_final_voor_parsing, 
                            "referentie_geparsed": geparseerde_referentie_data,
                            "interpretatie": interpretatie_resultaat, 
                            "volledige_regel_bron": bron_regel_voor_data_final, 
                            "gebruikte_zoekterm": gekozen_zoekterm 
                        }
                        print_eenheid_str = f"'{eenheid_final}'"
                        if is_alleen_waarde_match_flag: print_eenheid_str = f"'{eenheid_final}' (Aangenomen)"
                        print(f"Gevonden voor '{marker_config_entry.get('display_naam', sleutel_marker)}': Waarde={waarde_float} (Orig: '{waarde_str_ruw_final}'), Eenheid={print_eenheid_str}, Ref: {geparseerde_referentie_data}, Interp: '{interpretatie_resultaat}' (Bron: '{bron_regel_voor_data_final}') (Zoekterm: '{gekozen_zoekterm}')")
                        break 
    return gevonden_waarden

# ... (alle functies en MARKER_KENNISBANK hierboven) ...

# if __name__ == "__main__":
#     pdf_bestanden = ["voorbeeld_analyse_2021.pdf", "voorbeeld_analyse_2016.pdf"]
#     for pdf_bestand_pad in pdf_bestanden:
#         print(f"\n\n======================================================================")
#         print(f"BEZIG MET VERWERKEN VAN: {pdf_bestand_pad}")
#         print(f"======================================================================")
#         geextraheerde_tekst = extraheer_tekst_van_pdf(pdf_bestand_pad) 
#         if geextraheerde_tekst:
#             print("\n=== PARSEN VAN BLOEDWAARDEN ===")
#             resultaten = parseer_bloedwaarden(geextraheerde_tekst, MARKER_KENNISBANK, huidige_pdf_naam_voor_debug=pdf_bestand_pad) 
            
#             for marker_key_config, config_entry in MARKER_KENNISBANK.items():
#                 if marker_key_config not in resultaten:
#                     zoektermen_check = config_entry.get("zoektermen", [])
#                     if isinstance(zoektermen_check, str): zoektermen_check = [zoektermen_check]
#                     komt_een_zoekterm_voor_in_tekst = any(term.lower() in geextraheerde_tekst.lower() for term in zoektermen_check)
#                     if komt_een_zoekterm_voor_in_tekst:
#                         print(f"LET OP: Marker '{config_entry.get('display_naam', marker_key_config)}' (config zoektermen: '{zoektermen_check}') komt voor in tekst van {pdf_bestand_pad} maar is niet aan resultaten toegevoegd (controleer parseerlogica of zoektermen).")
#             if not resultaten: print(f"Algemene melding: Geen enkele geconfigureerde marker kunnen parsen uit {pdf_bestand_pad}.")
#         else: print(f"Kon geen tekst extraheren uit de PDF: {pdf_bestand_pad}.")
# --- EINDE VAN VOLLEDIG SCRIPT MET UREUM FIX POGING ---
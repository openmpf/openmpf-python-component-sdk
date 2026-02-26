#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2025 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2025 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################

from typing import Optional

class WtpLanguageSettings:
    # Supported languages and ISO 639-1, 639-2 codes for WtP models.
    # https://github.com/bminixhofer/wtpsplit?tab=readme-ov-file#supported-languages
    # https://www.loc.gov/standards/iso639-2/php/code_list.php
    _wtp_lang_map = {
        'afrikaans': 'af',
        'afr': 'af',
        'amharic': 'am',
        'amh': 'am',
        'arabic': 'ar',
        'ara': 'ar',
        'azerbaijani': 'az',
        'aze': 'az',
        'belarusian': 'be',
        'bel': 'be',
        'bulgarian': 'bg',
        'bul': 'bg',
        'bengali': 'bn',
        'ben': 'bn',
        'catalan': 'ca',
        'valencian': 'ca',
        'cat': 'ca',
        'cebuano': 'ceb', # In some cases, ISO-639-1 is not available, use ISO-639-2
        'ceb': 'ceb',
        'czech': 'cs',
        'cze': 'cs',
        'ces': 'cs',
        'welsh': 'cy',
        'wel': 'cy',
        'cym': 'cy',
        'danish': 'da',
        'dan': 'da',
        'german': 'de',
        'ger': 'de',
        'deu': 'de',
        'greek': 'el',
        'gre': 'el',
        'ell': 'el',
        'english': 'en',
        'eng': 'en',
        'esperanto': 'eo',
        'epo': 'eo',
        'spanish': 'es',
        'castilian': 'es',
        'spa': 'es',
        'estonian': 'et',
        'est': 'et',
        'basque': 'eu',
        'baq': 'eu',
        'eus': 'eu',
        'persian': 'fa',
        'per': 'fa',
        'fas': 'fa',
        'finnish': 'fi',
        'fin': 'fi',
        'french': 'fr',
        'fre': 'fr',
        'fra': 'fr',
        'western frisian': 'fy',
        'fry': 'fy',
        'irish': 'ga',
        'gle': 'ga',
        'gaelic': 'gd',
        'scottish gaelic': 'gd',
        'gla': 'gd',
        'galician': 'gl',
        'glg': 'gl',
        'gujarati': 'gu',
        'guj': 'gu',
        'hausa': 'ha',
        'hau': 'ha',
        'hebrew': 'he',
        'heb': 'he',
        'hindi': 'hi',
        'hin': 'hi',
        'hungarian': 'hu',
        'hun': 'hu',
        'armenian': 'hy',
        'arm': 'hy',
        'hye': 'hy',
        'indonesian': 'id',
        'ind': 'id',
        'igbo': 'ig',
        'ibo': 'ig',
        'icelandic': 'is',
        'ice': 'is',
        'isl': 'is',
        'italian': 'it',
        'ita': 'it',
        'japanese': 'ja',
        'jpn': 'ja',
        'javanese': 'jv',
        'jav': 'jv',
        'georgian': 'ka',
        'geo': 'ka',
        'kat': 'ka',
        'kazakh': 'kk',
        'kaz': 'kk',
        'central khmer': 'km',
        'khm': 'km',
        'kannada': 'kn',
        'kan': 'kn',
        'korean': 'ko',
        'kor': 'ko',
        'kurdish': 'ku',
        'kur': 'ku',
        'kirghiz': 'ky',
        'kyrgyz': 'ky',
        'kir': 'ky',
        'latin': 'la',
        'lat': 'la',
        'lithuanian': 'lt',
        'lit': 'lt',
        'latvian': 'lv',
        'lav': 'lv',
        'malagasy': 'mg',
        'mlg': 'mg',
        'macedonian': 'mk',
        'mac': 'mk',
        'mkd': 'mk',
        'malayalam': 'ml',
        'mal': 'ml',
        'mongolian': 'mn',
        'mon': 'mn',
        'marathi': 'mr',
        'mar': 'mr',
        'malay': 'ms',
        'may': 'ms',
        'msa': 'ms',
        'maltese': 'mt',
        'mlt': 'mt',
        'burmese': 'my',
        'bur': 'my',
        'mya': 'my',
        'nepali': 'ne',
        'nep': 'ne',
        'dutch': 'nl',
        'flemish': 'nl',
        'dut': 'nl',
        'nld': 'nl',
        'norwegian': 'no',
        'nor': 'no',
        'panjabi': 'pa',
        'punjabi': 'pa',
        'pan': 'pa',
        'polish': 'pl',
        'pol': 'pl',
        'pushto': 'ps',
        'pashto': 'ps',
        'pus': 'ps',
        'portuguese': 'pt',
        'por': 'pt',
        'romanian': 'ro',
        'moldavian': 'ro',
        'moldovan': 'ro',
        'rum': 'ro',
        'ron': 'ro',
        'russian': 'ru',
        'rus': 'ru',
        'sinhala': 'si',
        'sinhalese': 'si',
        'sin': 'si',
        'slovak': 'sk',
        'slo': 'sk',
        'slk': 'sk',
        'slovenian': 'sl',
        'slv': 'sl',
        'albanian': 'sq',
        'alb': 'sq',
        'sqi': 'sq',
        'serbian': 'sr',
        'srp': 'sr',
        'swedish': 'sv',
        'swe': 'sv',
        'tamil': 'ta',
        'tam': 'ta',
        'telugu': 'te',
        'tel': 'te',
        'tajik': 'tg',
        'tgk': 'tg',
        'thai': 'th',
        'tha': 'th',
        'turkish': 'tr',
        'tur': 'tr',
        'ukrainian': 'uk',
        'ukr': 'uk',
        'urdu': 'ur',
        'urd': 'ur',
        'uzbek': 'uz',
        'uzb': 'uz',
        'vietnamese': 'vi',
        'vie': 'vi',
        'xhosa': 'xh',
        'xho': 'xh',
        'yiddish': 'yi',
        'yid': 'yi',
        'yoruba': 'yo',
        'yor': 'yo',
        'chinese': 'zh',
        'chi': 'zh',
        'zho': 'zh',
        'zulu': 'zu',
        'zul': 'zu',
        'hans':'zh', # Also check for chinese scripts
        'hant': 'zh',
        'cmn':'zh' # In some cases we use 'cmn' = 'Mandarin'
    }

    # iso mappings for Flores-200 not recognized by
    # WtpLanguageSettings.convert_to_iso()
    _flores_to_wtpsplit_iso_639_1 = {
    'ace_arab': 'ar',   # Acehnese Arabic
    'ace_latn': 'id',   # Acehnese Latin
    'acm_arab': 'ar',   # Mesopotamian Arabic
    'acq_arab': 'ar',   # Ta’izzi-Adeni Arabic
    'aeb_arab': 'ar',   # Tunisian Arabic
    'ajp_arab': 'ar',   # South Levantine Arabic
    'aka_latn': 'ak',   # Akan
    'als_latn': 'sq',   # Albanian (Gheg)
    'apc_arab': 'ar',   # North Levantine Arabic
    'arb_arab': 'ar',   # Standard Arabic
    'arb_latn': 'ar',   # Standard Arabic (Latin script)
    'ars_arab': 'ar',   # Najdi Arabic
    'ary_arab': 'ar',   # Moroccan Arabic
    'arz_arab': 'ar',   # Egyptian Arabic
    'asm_beng': 'bn',   # Assamese
    'ast_latn': 'es',   # Asturian
    'awa_deva': 'hi',   # Awadhi
    'ayr_latn': 'es',   # Aymara
    'azb_arab': 'az',   # South Azerbaijani
    'azj_latn': 'az',   # North Azerbaijani
    'bak_cyrl': 'ru',   # Bashkir
    'bam_latn': 'fr',   # Bambara
    'ban_latn': 'id',   # Balinese
    'bem_latn': 'sw',   # Bemba
    'bho_deva': 'hi',   # Bhojpuri
    'bjn_latn': 'id',   # Banjar
    'bod_tibt': 'bo',   # Tibetan
    'bos_latn': 'bs',   # Bosnian
    'bug_latn': 'id',   # Buginese
    'cjk_latn': 'id',   # Chokwe (approx)
    'ckb_arab': 'ku',   # Central Kurdish (Sorani)
    'crh_latn': 'tr',   # Crimean Tatar
    'dik_latn': 'ar',   # Dinka
    'dyu_latn': 'fr',   # Dyula
    'dzo_tibt': 'dz',   # Dzongkha
    'ewe_latn': 'ee',   # Ewe
    'fao_latn': 'fo',   # Faroese
    'fij_latn': 'fj',   # Fijian
    'fon_latn': 'fr',   # Fon
    'fur_latn': 'it',   # Friulian
    'fuv_latn': 'ha',   # Nigerian Fulfulde
    'gaz_latn': 'om',   # Oromo
    'grn_latn': 'es',   # Guarani
    'hat_latn': 'fr',   # Haitian Creole
    'hne_deva': 'hi',   # Chhattisgarhi
    'hrv_latn': 'hr',   # Croatian
    'ilo_latn': 'tl',   # Ilocano
    'kab_latn': 'fr',   # Kabyle
    'kac_latn': 'my',   # Jingpho/Kachin
    'kam_latn': 'sw',   # Kamba
    'kas_deva': 'hi',   # Kashmiri
    'kbp_latn': 'fr',   # Kabiyè
    'kea_latn': 'pt',   # Cape Verdean Creole
    'khk_cyrl': 'mn',   # Halh Mongolian
    'kik_latn': 'sw',   # Kikuyu
    'kin_latn': 'rw',   # Kinyarwanda
    'kmb_latn': 'pt',   # Kimbundu
    'kmr_latn': 'ku',   # Kurmanji Kurdish
    'knc_latn': 'ha',   # Kanuri
    'kon_latn': 'fr',   # Kongo
    'lao_laoo': 'lo',   # Lao
    'lij_latn': 'it',   # Ligurian
    'lim_latn': 'nl',   # Limburgish
    'lin_latn': 'fr',   # Lingala
    'lmo_latn': 'it',   # Lombard
    'ltg_latn': 'lv',   # Latgalian
    'ltz_latn': 'lb',   # Luxembourgish
    'lua_latn': 'fr',   # Luba-Kasai
    'lug_latn': 'lg',   # Ganda
    'luo_latn': 'luo',  # Luo
    'lus_latn': 'hi',   # Mizo
    'lvs_latn': 'lv',   # Latvian
    'mag_deva': 'hi',   # Magahi
    'mai_deva': 'hi',   # Maithili
    'min_latn': 'id',   # Minangkabau
    'mni_beng': 'bn',   # Manipuri (Meitei)
    'mos_latn': 'fr',   # Mossi
    'mri_latn': 'mi',   # Maori
    'nno_latn': 'no',   # Norwegian Nynorsk
    'nob_latn': 'no',   # Norwegian Bokmål
    'npi_deva': 'ne',   # Nepali
    'nso_latn': 'st',   # Northern Sotho
    'nus_latn': 'ar',   # Nuer
    'nya_latn': 'ny',   # Chichewa
    'oci_latn': 'oc',   # Occitan
    'ory_orya': 'or',   # Odia
    'pag_latn': 'tl',   # Pangasinan
    'pap_latn': 'es',   # Papiamento
    'pbt_arab': 'ps',   # Southern Pashto
    'pes_arab': 'fa',   # Iranian Persian (Farsi)
    'plt_latn': 'mg',   # Plateau Malagasy
    'prs_arab': 'fa',   # Dari Persian
    'quy_latn': 'qu',   # Quechua
    'run_latn': 'rn',   # Rundi
    'sag_latn': 'fr',   # Sango
    'san_deva': 'sa',   # Sanskrit
    'sat_olck': 'hi',   # Santali
    'scn_latn': 'it',   # Sicilian
    'shn_mymr': 'my',   # Shan
    'smo_latn': 'sm',   # Samoan
    'sna_latn': 'sn',   # Shona
    'snd_arab': 'sd',   # Sindhi
    'som_latn': 'so',   # Somali
    'sot_latn': 'st',   # Southern Sotho
    'srd_latn': 'sc',   # Sardinian
    'ssw_latn': 'ss',   # Swati
    'sun_latn': 'su',   # Sundanese
    'swh_latn': 'sw',   # Swahili
    'szl_latn': 'pl',   # Silesian
    'taq_latn': 'ber',  # Tamasheq
    'tat_cyrl': 'tt',   # Tatar
    'tgl_latn': 'tl',   # Tagalog
    'tir_ethi': 'ti',   # Tigrinya
    'tpi_latn': 'tpi',  # Tok Pisin
    'tsn_latn': 'tn',   # Tswana
    'tso_latn': 'ts',   # Tsonga
    'tuk_latn': 'tk',   # Turkmen
    'tum_latn': 'ny',   # Tumbuka
    'twi_latn': 'ak',   # Twi
    'tzm_tfng': 'ber',  # Central Atlas Tamazight
    'uig_arab': 'ug',   # Uyghur
    'umb_latn': 'pt',   # Umbundu
    'uzn_latn': 'uz',   # Uzbek
    'vec_latn': 'it',   # Venetian
    'war_latn': 'tl',   # Waray
    'wol_latn': 'wo',   # Wolof
    'ydd_hebr': 'yi',   # Yiddish
    'yue_hant': 'zh',   # Yue Chinese (Cantonese)
    'zsm_latn': 'ms',   # Malay
    }


    _wtp_iso_set = set(_wtp_lang_map.values())

    @classmethod
    def convert_to_iso(cls, lang: Optional[str]) -> Optional[str]:
        # ISO 639-2 (language) is sometimes paired with ISO 15924 (script).
        # Extract the language portion and check if supported in WtP.
        if not lang:
            return None

        # 1) Handle Flores/NLLB codes first (e.g. "arb_Arab")
        norm = lang.strip().lower().replace('-', '_')
        mapped = cls._flores_to_wtpsplit_iso_639_1.get(norm)
        if mapped:
            lang = mapped

        if '-' in lang:
            lang = lang.split('-')[0]
        if '_' in lang:
            lang = lang.split('_')[0]

        lang = lang.strip().lower()

        if lang in cls._wtp_iso_set:
            return lang
        if lang in cls._wtp_lang_map:
            return cls._wtp_lang_map[lang]
        return None

"""Read a daftar nilai workbook into a student roster.

Expected shape, matching DAFTAR NILAI INFORMATIKA GANJIL:
- one worksheet per class (7.1, 7.2, ...), or one sheet with class section rows
- a header row that contains a name column (Nama / Nama Siswa / Nama Peserta Didik)
- optional NIS / NISN and L/P columns
"""

import re

import pandas as pd

CLASS_RE = re.compile(r"(?:kelas\s*)?([7-9])\s*[\.\-]\s*(\d+)", re.IGNORECASE)
ROMAN = (("viii", "8"), ("vii", "7"), ("ix", "9"))

NAMA_HEADERS = ("nama peserta didik", "nama siswa", "nama lengkap", "nama")
NIS_HEADERS = ("nisn", "nis", "no induk")
JK_HEADERS = ("l/p", "l / p", "jk", "jenis kelamin", "kelamin")


def normalize_name(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text


def name_key(value):
    return normalize_name(value).casefold()


def normalize_class(value):
    text = str(value or "").strip().lower()
    if not text or text == "nan":
        return None
    for roman, digit in ROMAN:
        text = text.replace(roman, digit)
    match = CLASS_RE.search(text)
    if not match:
        return None
    return f"{match.group(1)}.{int(match.group(2))}"


def parse_nis(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return "" if text.lower() == "nan" else text


def parse_jk(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().upper()
    if text in ("L", "LAKI-LAKI", "LAKI", "M"):
        return "L"
    if text in ("P", "PEREMPUAN", "W"):
        return "P"
    return None


def _header_index(cells, names):
    normalized = [re.sub(r"\s+", " ", str(cell or "")).strip().lower() for cell in cells]
    for wanted in names:
        for index, cell in enumerate(normalized):
            if cell == wanted or cell.startswith(wanted + " "):
                return index
    return None


def _row_values(row):
    values = []
    for cell in row:
        if cell is None or (isinstance(cell, float) and pd.isna(cell)):
            values.append("")
        else:
            values.append(cell)
    return values


def _is_section_row(values):
    texts = [str(v).strip() for v in values if str(v).strip()]
    if len(texts) != 1:
        return None
    return normalize_class(texts[0])


def parse_workbook(file_obj):
    sheets = pd.read_excel(file_obj, sheet_name=None, header=None, dtype=object)
    students = []
    notes = []

    for sheet_name, frame in sheets.items():
        current_class = normalize_class(sheet_name)
        columns = None
        found_header = False
        sheet_count = 0

        for row in frame.itertuples(index=False, name=None):
            values = _row_values(row)
            section = _is_section_row(values)
            if section:
                current_class = section
                columns = None
                continue

            nama_at = _header_index(values, NAMA_HEADERS)
            if nama_at is not None:
                # A data row can contain the word "nama" inside a student's name.
                # Treat the row as a header only when the name cell is exactly a header label.
                label = re.sub(r"\s+", " ", str(values[nama_at] or "")).strip().lower()
                if label in NAMA_HEADERS:
                    columns = {
                        "nama": nama_at,
                        "nis": _header_index(values, NIS_HEADERS),
                        "jk": _header_index(values, JK_HEADERS),
                        "kelas": _header_index(values, ("kelas",)),
                    }
                    found_header = True
                    continue

            if not columns:
                continue

            nama = normalize_name(values[columns["nama"]]) if columns["nama"] < len(values) else ""
            if not nama or name_key(nama) in ("nama", "nama siswa", "jumlah", "total"):
                continue
            if nama.lower().startswith("jumlah"):
                continue

            row_class = current_class
            if columns.get("kelas") is not None and columns["kelas"] < len(values):
                row_class = normalize_class(values[columns["kelas"]]) or current_class
            if not row_class:
                notes.append(f"Sheet '{sheet_name}': '{nama}' dilewati karena kelas tidak dikenali.")
                continue
            current_class = row_class

            nis = ""
            if columns["nis"] is not None and columns["nis"] < len(values):
                nis = parse_nis(values[columns["nis"]])
            jk = None
            if columns["jk"] is not None and columns["jk"] < len(values):
                jk = parse_jk(values[columns["jk"]])

            students.append({
                "kelas": current_class,
                "nama": nama,
                "nis": nis,
                "jk": jk,
            })
            sheet_count += 1

        if not found_header:
            notes.append(f"Sheet '{sheet_name}' dilewati: kolom Nama tidak ditemukan.")
        elif sheet_count == 0:
            notes.append(f"Sheet '{sheet_name}' tidak berisi siswa.")

    return students, notes

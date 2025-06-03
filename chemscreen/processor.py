"""Chemical processor module for validation and standardization."""

import re
from typing import List, Optional, Tuple, Dict, Any
import logging
import pandas as pd
from io import StringIO

from chemscreen.models import Chemical, CSVUploadResult, CSVColumnMapping
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def validate_cas_number(cas: str) -> bool:
    """
    Validate CAS Registry Number format and checksum.

    CAS format: XXXXXX-XX-X where X is a digit.
    The last digit is a check digit.

    Args:
        cas: CAS number string

    Returns:
        bool: True if valid CAS number
    """
    # Remove any spaces
    cas = cas.strip().replace(" ", "")

    # Check format
    pattern = r"^\d{2,7}-\d{2}-\d$"
    if not re.match(pattern, cas):
        return False

    # Extract digits for checksum validation
    parts = cas.split("-")
    digits = parts[0] + parts[1]
    check_digit = int(parts[2])

    # Calculate checksum
    total = 0
    for i, digit in enumerate(reversed(digits)):
        total += (i + 1) * int(digit)

    calculated_check = total % 10

    return calculated_check == check_digit


def standardize_chemical_name(name: str) -> str:
    """
    Standardize chemical name formatting.

    Args:
        name: Chemical name

    Returns:
        str: Standardized name
    """
    # Strip whitespace
    name = name.strip()

    # Normalize whitespace
    name = " ".join(name.split())

    # Convert to title case for consistency
    # But preserve certain patterns like TCE, NMP
    if name.isupper() and len(name) <= 5:
        return name

    return name


def parse_chemical_list(
    data: List[dict],
    name_column: Optional[str] = None,
    cas_column: Optional[str] = None,
) -> List[Chemical]:
    """
    Parse a list of chemical data into Chemical objects.

    Args:
        data: List of dictionaries from CSV
        name_column: Column name for chemical names
        cas_column: Column name for CAS numbers

    Returns:
        List[Chemical]: Parsed and validated chemicals
    """
    chemicals = []

    for idx, row in enumerate(data):
        # Extract name and CAS
        name = None
        cas = None

        if name_column and name_column in row:
            name = str(row[name_column]).strip()

        if cas_column and cas_column in row:
            cas = str(row[cas_column]).strip()

        # Try to infer if columns not specified
        if not name_column:
            # Look for common name columns
            for col in ["name", "chemical_name", "chemical", "compound"]:
                if col in row:
                    name = str(row[col]).strip()
                    break

        if not cas_column:
            # Look for common CAS columns
            for col in ["cas", "cas_number", "cas_no", "casrn"]:
                if col in row:
                    cas = str(row[col]).strip()
                    break

        # Skip if no name or CAS
        if not name and not cas:
            logger.warning(f"Row {idx + 1}: No chemical name or CAS number found")
            continue

        # Validate CAS if provided
        validated = True
        if cas:
            validated = validate_cas_number(cas)
            if not validated:
                logger.warning(f"Row {idx + 1}: Invalid CAS number format: {cas}")

        # Create Chemical object
        chemical = Chemical(
            name=standardize_chemical_name(name) if name else f"CAS {cas}",
            cas_number=cas if cas else None,
            validated=validated,
            notes=None,
        )

        chemicals.append(chemical)

    return chemicals


def detect_duplicates(chemicals: List[Chemical]) -> List[Tuple[int, int]]:
    """
    Detect duplicate chemicals based on name or CAS.

    Args:
        chemicals: List of Chemical objects

    Returns:
        List of tuples with duplicate indices
    """
    duplicates = []

    # Check by CAS number first (more reliable)
    cas_map: Dict[str, int] = {}
    for i, chem in enumerate(chemicals):
        if chem.cas_number:
            if chem.cas_number in cas_map:
                duplicates.append((cas_map[chem.cas_number], i))
            else:
                cas_map[chem.cas_number] = i

    # Check by name (case insensitive)
    name_map: Dict[str, int] = {}
    for i, chem in enumerate(chemicals):
        name_lower = chem.name.lower()
        if name_lower in name_map:
            # Only flag as duplicate if not already flagged by CAS
            if not any(dup[1] == i for dup in duplicates):
                duplicates.append((name_map[name_lower], i))
        else:
            name_map[name_lower] = i

    return duplicates


def merge_duplicates(chemicals: List[Chemical]) -> List[Chemical]:
    """
    Merge duplicate chemicals, preserving all information.

    Args:
        chemicals: List of Chemical objects

    Returns:
        List[Chemical]: Deduplicated list
    """
    # Find duplicates
    duplicates = detect_duplicates(chemicals)

    if not duplicates:
        return chemicals

    # Mark indices to skip
    skip_indices = {dup[1] for dup in duplicates}

    # Build merged list
    merged = []
    for i, chem in enumerate(chemicals):
        if i not in skip_indices:
            merged.append(chem)

    logger.info(f"Merged {len(duplicates)} duplicate chemicals")

    return merged


# Common chemical abbreviations and their full names
CHEMICAL_ABBREVIATIONS = {
    "TCE": "Trichloroethylene",
    "PCE": "Tetrachloroethylene",
    "DCM": "Dichloromethane",
    "MEK": "Methyl ethyl ketone",
    "NMP": "N-Methylpyrrolidone",
    "THF": "Tetrahydrofuran",
    "DMF": "Dimethylformamide",
    "DMSO": "Dimethyl sulfoxide",
    "IPA": "Isopropyl alcohol",
    "EtOH": "Ethanol",
    "MeOH": "Methanol",
    "ACN": "Acetonitrile",
}


def expand_abbreviations(name: str) -> Tuple[str, List[str]]:
    """
    Expand common chemical abbreviations to full names.

    Args:
        name: Chemical name or abbreviation

    Returns:
        Tuple of (primary name, list of synonyms)
    """
    name_upper = name.upper()

    if name_upper in CHEMICAL_ABBREVIATIONS:
        full_name = CHEMICAL_ABBREVIATIONS[name_upper]
        return full_name, [name]

    return name, []


def process_csv_data(
    df: pd.DataFrame,
    column_mapping: CSVColumnMapping,
) -> CSVUploadResult:
    """
    Process CSV data into validated Chemical objects.

    Args:
        df: DataFrame containing CSV data
        column_mapping: Column mapping configuration

    Returns:
        CSVUploadResult with validated chemicals and error information
    """
    result = CSVUploadResult(
        total_rows=len(df),
        column_mapping={
            "name": column_mapping.name_column or "",
            "cas": column_mapping.cas_column or "",
            "synonyms": column_mapping.synonyms_column or "",
            "notes": column_mapping.notes_column or "",
        },
    )

    # Process each row
    for idx, row in df.iterrows():
        try:
            # Convert idx to int for arithmetic operations
            row_num = int(str(idx)) + 1
            # Extract data based on column mapping
            chemical_data: Dict[str, Any] = {}

            # Name (required if no CAS)
            if column_mapping.name_column:
                name = str(row.get(column_mapping.name_column, "")).strip()
                if name and name.lower() not in ["nan", "none", "null"]:
                    chemical_data["name"] = name

            # CAS number (required if no name)
            if column_mapping.cas_column:
                cas = str(row.get(column_mapping.cas_column, "")).strip()
                if cas and cas.lower() not in ["nan", "none", "null"]:
                    chemical_data["cas_number"] = cas

            # Optional fields
            if column_mapping.synonyms_column:
                synonyms = str(row.get(column_mapping.synonyms_column, "")).strip()
                if synonyms and synonyms.lower() not in ["nan", "none", "null"]:
                    # Split synonyms by common delimiters
                    syn_list = re.split(r"[;,|]", synonyms)
                    chemical_data["synonyms"] = [
                        s.strip() for s in syn_list if s.strip()
                    ]
            else:
                chemical_data["synonyms"] = []

            if column_mapping.notes_column:
                notes = str(row.get(column_mapping.notes_column, "")).strip()
                if notes and notes.lower() not in ["nan", "none", "null"]:
                    chemical_data["notes"] = notes

            # Skip empty rows
            if not chemical_data.get("name") and not chemical_data.get("cas_number"):
                result.warnings.append(
                    f"Row {row_num}: Skipped - no chemical name or CAS number"
                )
                continue

            # If we have a name but no CAS, or vice versa, provide a default
            if not chemical_data.get("name") and chemical_data.get("cas_number"):
                chemical_data["name"] = (
                    f"Chemical with CAS {chemical_data['cas_number']}"
                )
            elif chemical_data.get("name") and not chemical_data.get("cas_number"):
                # Name exists, CAS is optional
                pass

            # Expand abbreviations if applicable
            if chemical_data.get("name"):
                expanded_name, abbrev_synonyms = expand_abbreviations(
                    chemical_data["name"]
                )
                if expanded_name != chemical_data["name"]:
                    chemical_data["name"] = expanded_name
                    existing_synonyms: List[str] = chemical_data.get("synonyms", [])
                    chemical_data["synonyms"] = list(
                        set(existing_synonyms + abbrev_synonyms)
                    )

            # Create and validate Chemical object
            chemical = Chemical(**chemical_data)

            # Additional CAS validation with checksum
            if chemical.cas_number:
                if validate_cas_number(chemical.cas_number):
                    chemical.validated = True
                else:
                    chemical.validated = False
                    result.warnings.append(
                        f"Row {row_num}: CAS number {chemical.cas_number} failed checksum validation"
                    )
            else:
                # No CAS number to validate
                chemical.validated = True

            result.valid_chemicals.append(chemical)

        except ValidationError as e:
            # Pydantic validation error
            error_details = {
                "row_number": row_num,
                "row_data": row.to_dict(),
                "errors": [
                    {"field": err["loc"][0], "message": err["msg"]}
                    for err in e.errors()
                ],
            }
            result.invalid_rows.append(error_details)
            logger.error(f"Row {row_num} validation error: {e}")

        except Exception as e:
            # Other unexpected errors
            error_details = {
                "row_number": row_num,
                "row_data": row.to_dict(),
                "errors": [{"field": "unknown", "message": str(e)}],
            }
            result.invalid_rows.append(error_details)
            logger.error(f"Row {row_num} processing error: {e}")

    # Check for duplicates
    if result.valid_chemicals:
        duplicates = detect_duplicates(result.valid_chemicals)
        if duplicates:
            for dup1, dup2 in duplicates:
                chem1 = result.valid_chemicals[dup1]
                chem2 = result.valid_chemicals[dup2]
                result.warnings.append(
                    f"Duplicate detected: '{chem1.name}' (index {dup1}) "
                    f"and '{chem2.name}' (index {dup2})"
                )

    return result


def validate_csv_file(
    file_content: str, delimiter: str = ",", encoding: str = "utf-8"
) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
    """
    Validate CSV file format and structure.

    Args:
        file_content: CSV file content as string
        delimiter: CSV delimiter
        encoding: File encoding

    Returns:
        Tuple of (is_valid, dataframe, error_message)
    """
    try:
        # Try to read CSV
        df = pd.read_csv(StringIO(file_content), delimiter=delimiter)

        # Check if empty
        if df.empty:
            return False, None, "CSV file is empty"

        # Check if has columns
        if len(df.columns) == 0:
            return False, None, "CSV file has no columns"

        # Check for at least 1 data row
        if len(df) == 0:
            return False, None, "CSV file has no data rows"

        return True, df, None

    except pd.errors.EmptyDataError:
        return False, None, "CSV file is empty or invalid"
    except pd.errors.ParserError as e:
        return False, None, f"CSV parsing error: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error reading CSV: {str(e)}"


def suggest_column_mapping(df: pd.DataFrame) -> CSVColumnMapping:
    """
    Suggest column mapping based on column names.

    Args:
        df: DataFrame with CSV data

    Returns:
        CSVColumnMapping with suggested mappings
    """
    columns_lower = {col.lower(): col for col in df.columns}

    # Try to find name column
    name_column = None
    for pattern in ["name", "chemical_name", "chemical name", "compound", "substance"]:
        if pattern in columns_lower:
            name_column = columns_lower[pattern]
            break

    # Try to find CAS column
    cas_column = None
    for pattern in ["cas", "cas_number", "cas number", "cas_no", "casrn", "cas rn"]:
        if pattern in columns_lower:
            cas_column = columns_lower[pattern]
            break

    # Try to find synonyms column
    synonyms_column = None
    for pattern in ["synonyms", "synonym", "alternative names", "other names"]:
        if pattern in columns_lower:
            synonyms_column = columns_lower[pattern]
            break

    # Try to find notes column
    notes_column = None
    for pattern in ["notes", "note", "comments", "comment", "remarks"]:
        if pattern in columns_lower:
            notes_column = columns_lower[pattern]
            break

    return CSVColumnMapping(
        name_column=name_column,
        cas_column=cas_column,
        synonyms_column=synonyms_column,
        notes_column=notes_column,
    )

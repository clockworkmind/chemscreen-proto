"""Chemical processor module for validation and standardization."""

import re
from typing import List, Optional, Tuple, Dict
import logging

from chemscreen.models import Chemical

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

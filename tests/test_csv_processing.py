"""Tests for CSV processing functionality."""

import pandas as pd

from chemscreen.processor import (
    validate_cas_number,
    standardize_chemical_name,
    expand_abbreviations,
    process_csv_data,
    validate_csv_file,
    suggest_column_mapping,
    detect_duplicates,
    merge_duplicates,
)
from chemscreen.models import Chemical, CSVColumnMapping


class TestCASValidation:
    """Test CAS number validation."""

    def test_valid_cas_numbers(self):
        """Test valid CAS numbers pass validation."""
        valid_cases = [
            "75-09-2",  # Dichloromethane
            "79-01-6",  # TCE
            "71-43-2",  # Benzene
            "50-00-0",  # Formaldehyde
            "7732-18-5",  # Water
        ]
        for cas in valid_cases:
            assert validate_cas_number(cas) is True, f"Failed for {cas}"

    def test_invalid_cas_numbers(self):
        """Test invalid CAS numbers fail validation."""
        invalid_cases = [
            "75-09-3",  # Wrong checksum
            "123456",  # No hyphens
            "12-34-56",  # Wrong format
            "1-2-3",  # Too short
            "abc-12-3",  # Non-numeric
            "",  # Empty
        ]
        for cas in invalid_cases:
            assert validate_cas_number(cas) is False, f"Should fail for {cas}"


class TestChemicalNameProcessing:
    """Test chemical name standardization."""

    def test_standardize_names(self):
        """Test name standardization."""
        cases = [
            ("  benzene  ", "benzene"),
            ("BENZENE", "BENZENE"),
            ("methyl  ethyl  ketone", "methyl ethyl ketone"),
            ("TCE", "TCE"),  # Preserves short uppercase
            ("Dichloromethane", "Dichloromethane"),
        ]
        for input_name, expected in cases:
            assert standardize_chemical_name(input_name) == expected

    def test_expand_abbreviations(self):
        """Test abbreviation expansion."""
        cases = [
            ("TCE", ("Trichloroethylene", ["TCE"])),
            ("DCM", ("Dichloromethane", ["DCM"])),
            ("Benzene", ("Benzene", [])),
            ("Unknown", ("Unknown", [])),
        ]
        for abbrev, expected in cases:
            assert expand_abbreviations(abbrev) == expected


class TestCSVProcessing:
    """Test CSV data processing."""

    def test_process_valid_csv(self):
        """Test processing valid CSV data."""
        df = pd.DataFrame(
            {
                "Chemical": ["Benzene", "TCE", "Formaldehyde"],
                "CAS": ["71-43-2", "79-01-6", "50-00-0"],
                "Notes": ["Solvent", "Degreaser", "Preservative"],
            }
        )

        mapping = CSVColumnMapping(
            name_column="Chemical", cas_column="CAS", notes_column="Notes"
        )

        result = process_csv_data(df, mapping)

        assert result.total_rows == 3
        assert len(result.valid_chemicals) == 3
        assert len(result.invalid_rows) == 0
        assert result.success_rate == 100.0

        # Check first chemical
        chem = result.valid_chemicals[0]
        assert chem.name == "Benzene"
        assert chem.cas_number == "71-43-2"
        assert chem.notes == "Solvent"
        assert chem.validated is True

    def test_process_invalid_cas(self):
        """Test processing with invalid CAS numbers."""
        df = pd.DataFrame(
            {"Name": ["Chemical 1", "Chemical 2"], "CAS": ["71-43-2", "invalid-cas"]}
        )

        mapping = CSVColumnMapping(name_column="Name", cas_column="CAS")
        result = process_csv_data(df, mapping)

        assert result.total_rows == 2
        assert len(result.valid_chemicals) == 1  # Only valid CAS passes
        assert len(result.invalid_rows) == 1  # Invalid CAS is rejected
        assert result.valid_chemicals[0].validated is True
        assert result.invalid_rows[0]["row_number"] == 2

    def test_process_invalid_cas_checksum(self):
        """Test processing with CAS numbers that fail checksum."""
        df = pd.DataFrame(
            {
                "Name": ["Chemical 1", "Chemical 2"],
                "CAS": ["71-43-2", "71-43-3"],  # Second has wrong checksum
            }
        )

        mapping = CSVColumnMapping(name_column="Name", cas_column="CAS")
        result = process_csv_data(df, mapping)

        assert result.total_rows == 2
        assert len(result.valid_chemicals) == 2  # Both have valid format
        assert result.valid_chemicals[0].validated is True
        assert result.valid_chemicals[1].validated is False  # Checksum failed
        assert len(result.warnings) == 1
        assert "failed checksum validation" in result.warnings[0]

    def test_process_missing_data(self):
        """Test processing with missing data."""
        df = pd.DataFrame(
            {
                "Name": ["Chemical 1", "", "Chemical 3"],
                "CAS": ["71-43-2", "75-09-2", ""],
            }
        )

        mapping = CSVColumnMapping(name_column="Name", cas_column="CAS")
        result = process_csv_data(df, mapping)

        assert len(result.valid_chemicals) == 3
        # Second chemical should have generated name
        assert result.valid_chemicals[1].name == "Chemical with CAS 75-09-2"

    def test_abbreviation_expansion(self):
        """Test that abbreviations are expanded during processing."""
        df = pd.DataFrame(
            {
                "Name": ["TCE", "DCM", "Benzene"],
                "CAS": ["79-01-6", "75-09-2", "71-43-2"],
            }
        )

        mapping = CSVColumnMapping(name_column="Name", cas_column="CAS")
        result = process_csv_data(df, mapping)

        assert result.valid_chemicals[0].name == "Trichloroethylene"
        assert "TCE" in result.valid_chemicals[0].synonyms
        assert result.valid_chemicals[1].name == "Dichloromethane"
        assert "DCM" in result.valid_chemicals[1].synonyms
        assert result.valid_chemicals[2].name == "Benzene"


class TestDuplicateDetection:
    """Test duplicate detection and merging."""

    def test_detect_duplicates_by_cas(self):
        """Test duplicate detection by CAS number."""
        chemicals = [
            Chemical(name="Benzene", cas_number="71-43-2"),
            Chemical(name="Benzol", cas_number="71-43-2"),
            Chemical(name="Toluene", cas_number="108-88-3"),
        ]

        duplicates = detect_duplicates(chemicals)
        assert len(duplicates) == 1
        assert duplicates[0] == (0, 1)  # First two are duplicates

    def test_detect_duplicates_by_name(self):
        """Test duplicate detection by name."""
        chemicals = [
            Chemical(name="Benzene"),
            Chemical(name="BENZENE"),
            Chemical(name="Toluene"),
        ]

        duplicates = detect_duplicates(chemicals)
        assert len(duplicates) == 1
        assert duplicates[0] == (0, 1)  # Case-insensitive match

    def test_merge_duplicates(self):
        """Test duplicate merging."""
        chemicals = [
            Chemical(name="Benzene", cas_number="71-43-2"),
            Chemical(name="Benzol", cas_number="71-43-2"),
            Chemical(name="Toluene", cas_number="108-88-3"),
        ]

        merged = merge_duplicates(chemicals)
        assert len(merged) == 2
        assert merged[0].name == "Benzene"
        assert merged[1].name == "Toluene"


class TestCSVValidation:
    """Test CSV file validation."""

    def test_valid_csv(self):
        """Test valid CSV passes validation."""
        csv_content = "Name,CAS\nBenzene,71-43-2\nToluene,108-88-3"
        is_valid, df, error = validate_csv_file(csv_content)

        assert is_valid is True
        assert df is not None
        assert error is None
        assert len(df) == 2

    def test_empty_csv(self):
        """Test empty CSV fails validation."""
        csv_content = ""
        is_valid, df, error = validate_csv_file(csv_content)

        assert is_valid is False
        assert df is None
        assert "empty" in error.lower()

    def test_malformed_csv(self):
        """Test malformed CSV fails validation."""
        csv_content = 'Name,CAS\n"Benzene,71-43-2'  # Unclosed quote
        is_valid, df, error = validate_csv_file(csv_content)

        assert is_valid is False
        assert df is None
        assert error is not None


class TestColumnMapping:
    """Test column mapping suggestion."""

    def test_suggest_standard_columns(self):
        """Test suggestion for standard column names."""
        df = pd.DataFrame(
            {"Chemical Name": [], "CAS Number": [], "Synonyms": [], "Notes": []}
        )

        mapping = suggest_column_mapping(df)
        assert mapping.name_column == "Chemical Name"
        assert mapping.cas_column == "CAS Number"
        assert mapping.synonyms_column == "Synonyms"
        assert mapping.notes_column == "Notes"

    def test_suggest_alternate_columns(self):
        """Test suggestion for alternate column names."""
        df = pd.DataFrame(
            {"compound": [], "casrn": [], "alternative names": [], "comments": []}
        )

        mapping = suggest_column_mapping(df)
        assert mapping.name_column == "compound"
        assert mapping.cas_column == "casrn"
        assert mapping.synonyms_column == "alternative names"
        assert mapping.notes_column == "comments"

    def test_suggest_case_insensitive(self):
        """Test case-insensitive column matching."""
        df = pd.DataFrame({"NAME": [], "cas": [], "SYNONYMS": [], "Notes": []})

        mapping = suggest_column_mapping(df)
        assert mapping.name_column == "NAME"
        assert mapping.cas_column == "cas"
        assert mapping.synonyms_column == "SYNONYMS"
        assert mapping.notes_column == "Notes"

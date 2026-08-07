import os
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from rdflib import Graph, Namespace
from src.exporter.rdf_exporter import export_to_turtle


@pytest.fixture
def dummy_rdf_df():
    """Provides a dummy DataFrame that simulates the output from the database."""
    return pd.DataFrame([{
        'review_id': 1,
        'claim_id': 10,
        'portal_id': 100,
        'claim': 'Der Himmel ist grün.',
        'language': 'de',
        'claim_author': 'Max Mustermann',
        'stated_at': '30.07.2026',
        'headline': 'Faktencheck: Himmel ist blau',
        'article_url': 'https://testportal.com/fc',
        'rating_original': 'Falsch',
        'portal_name': 'Test Portal'
    }])


@pytest.fixture
def mock_db(dummy_rdf_df):
    """Mocks the FactCheckManager to skip database queries."""
    db = MagicMock()
    db.get_rdf_export_data.return_value = dummy_rdf_df
    return db


@patch('src.exporter.rdf_exporter.logger.error')
def test_export_db_error(mock_error, mock_db, tmp_path):
    """Checks whether a database error is properly handled and logged."""
    mock_db.get_rdf_export_data.side_effect = Exception("Database connection lost")
    output_file = tmp_path / "test.ttl"

    export_to_turtle(mock_db, str(output_file))

    mock_error.assert_called_once()
    assert "Error loading the database" in mock_error.call_args[0][0]
    assert not os.path.exists(output_file)


@patch('src.exporter.rdf_exporter.logger.info')
def test_export_empty_data(mock_info, mock_db, tmp_path):
    """Checks whether an empty DataFrame is detected and whether the export is cancelled."""
    mock_db.get_rdf_export_data.return_value = pd.DataFrame()
    output_file = tmp_path / "test.ttl"

    export_to_turtle(mock_db, str(output_file))

    mock_info.assert_called_once_with("No data found for the RDF export.")
    assert not os.path.exists(output_file)


@patch('src.exporter.rdf_exporter.logger.info')
def test_export_success_and_graph_structure(mock_info, mock_db, tmp_path):
    """Test that the export was successful and check the structure of the generated graph."""
    output_file = tmp_path / "output" / "faktenchecks_export.ttl"

    export_to_turtle(mock_db, str(output_file))

    assert os.path.exists(output_file)
    mock_info.assert_called_with(f"Exported 1 rows to {output_file}")

    g = Graph()
    g.parse(str(output_file), format="turtle")

    assert len(g) > 0, "Der generierte Graph sollte nicht leer sein."

    CKG = Namespace("http://data.gesis.org/claimskg/")
    SCHEMA = Namespace("https://schema.org/")

    review_uri = CKG["review_1_10"]
    prop_uri = CKG["proposition_10"]
    rating_uri = CKG["rating_1_10"]

    assert (review_uri, SCHEMA.itemReviewed, prop_uri) in g
    assert (review_uri, SCHEMA.reviewRating, rating_uri) in g


def test_export_date_format_fallback(mock_db, dummy_rdf_df, tmp_path):
    """Tests the try/except block for incorrect date formats."""
    dummy_rdf_df.at[0, 'stated_at'] = 'date'
    mock_db.get_rdf_export_data.return_value = dummy_rdf_df
    output_file = tmp_path / "test_fallback.ttl"
    export_to_turtle(mock_db, str(output_file))

    g = Graph()
    g.parse(str(output_file), format="turtle")
    CKG = Namespace("http://data.gesis.org/claimskg/")
    SCHEMA = Namespace("https://schema.org/")
    context_uri = CKG["context_10"]

    date_objects = list(g.objects(context_uri, SCHEMA.dateCreated))

    assert len(date_objects) == 1
    assert date_objects[0].datatype is None
    assert str(date_objects[0]) == "date"
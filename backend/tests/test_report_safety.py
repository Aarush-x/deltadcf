from src.data.bse_fetcher import clean_bse_symbol
from src.data.report_processor import ReportProcessor


def test_bse_symbol_suffixes_are_removed():
    assert clean_bse_symbol("INFY.NS") == "INFY"
    assert clean_bse_symbol("INFY.BO") == "INFY"
    assert clean_bse_symbol("AAPL") == "AAPL"


def test_temporary_report_cleanup(tmp_path):
    report_path = tmp_path / "report.pdf"
    report_path.write_bytes(b"temporary report")

    ReportProcessor.cleanup_download(report_path)

    assert not report_path.exists()

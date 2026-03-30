class DescriptionMappingError(ValueError):
    """Structured loader error with an optional source span for diagnostics."""

    def __init__(self, message: str, *, span: SourceSpan | None = None):
        super().__init__(message)
        self.message = message
        self.span = span

    def __str__(self) -> str:
        if self.span is None:
            return self.message
        return f"{self.message} ({self.span.format()})"


""" Start move to File mainFiles/_load_description_mapping.py
import src
"""
def _load_description_mapping(path: str) -> dict[str, str]:
    return load_description_mapping(
        path,
        description_mapping_error_cls=DescriptionMappingError,
        source_span_cls=SourceSpan,
        get_base_name_from_file=get_base_name_from_file,
    )
""" End move to File mainFiles/_load_description_mapping.py """


""" Start move to File mainFiles/_load_description_mappingFiles/_load_description_mapping_from_csv.py
import src
"""
def _load_description_mapping_from_csv(path: str) -> dict[str, str]:
    return load_description_mapping_from_csv(
        path,
        description_mapping_error_cls=DescriptionMappingError,
        source_span_cls=SourceSpan,
    )
""" End move to File mainFiles/_load_description_mappingFiles/_load_description_mapping_from_csv.py """


""" Start move to File mainFiles/_load_description_mappingFiles/_load_description_mapping_from_xml.py
import src
"""
def _load_description_mapping_from_xml(path: str) -> dict[str, str]:
    return load_description_mapping_from_xml(
        path,
        description_mapping_error_cls=DescriptionMappingError,
        source_span_cls=SourceSpan,
        get_base_name_from_file=get_base_name_from_file,
    )
""" End move to File mainFiles/_load_description_mappingFiles/_load_description_mapping_from_xml.py """


""" Start move to File mainFiles/_resolve_cli_csv_and_outputFiles/_resolve_description_xml_path.py
import src
"""
def _resolve_description_xml_path(path: str) -> str | None:
    return resolve_description_xml_path(path)
""" End move to File mainFiles/_resolve_cli_csv_and_outputFiles/_resolve_description_xml_path.py """


""" Start move to File mainFiles/build_linux_vendor_install_commandFiles/_required_vendor_packages.py
import src
"""
def _required_vendor_packages() -> list[str]:
    return [
        "numpy",
        "opencv-python-headless",
        "Pillow",
        "PyMuPDF",
    ]
""" End move to File mainFiles/build_linux_vendor_install_commandFiles/_required_vendor_packages.py """


""" Start move to File mainFiles/build_linux_vendor_install_command.py
import src
"""

from src import image_composite_converter as _icc

globals().update(vars(_icc))

def build_linux_vendor_install_command(
    vendor_dir: str = "vendor",
    platform_tag: str = "manylinux2014_x86_64",
    python_version: str | None = None,
) -> list[str]:
    if python_version is None:
        python_version = f"{sys.version_info.major}{sys.version_info.minor}"

    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        vendor_dir,
        "--platform",
        platform_tag,
        "--implementation",
        "cp",
        "--python-version",
        python_version,
        "--only-binary=:all:",
        "--upgrade-strategy",
        "eager",
        *_required_vendor_packages(),
    ]

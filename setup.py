"""Setup script for mcp-scotty."""

from setuptools import setup, find_packages

setup(
    name="mcp-scotty",
    version="0.4.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.2.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-scotty=mcp_scotty.server:main",
        ],
    },
)

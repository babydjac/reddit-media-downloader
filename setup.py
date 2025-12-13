"""Setup configuration for Reddit Media Downloader."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="reddit-media-downloader",
    version="1.0.0",
    author="babydjac",
    description="Robust, modern Reddit media downloader CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/babydjac/reddit-media-downloader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "reddit=reddit_media_downloader.cli:main",
        ],
    },
)

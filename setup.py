"""Setup configuration for AutoGS package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="autogs",
    version="0.1.0",
    author="AutoGS Team",
    author_email="autogs@example.com",
    description="Automated Game Studio - AI-powered Unity game development pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autogs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.5.0"],
        "full": [
            "openai>=1.0.0",
            "anthropic>=0.5.0",
            "httpx>=0.24.0",
            "aiohttp>=3.8.0",
            "rich>=13.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autogs=autogs.__main__:main",
        ],
    },
)

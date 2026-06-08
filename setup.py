from setuptools import setup, find_packages

setup(
    name="homecastr",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-httpx>=0.30.0",
            "ruff>=0.4.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "matplotlib>=3.8.0",
            "h3>=4.0.0",
        ],
    },
    python_requires=">=3.9",
    author="Homecastr",
    author_email="api@homecastr.com",
    description="Python SDK for the Homecastr probabilistic home value forecast API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/homecastr/homecastr-python",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: GIS",
    ],
)

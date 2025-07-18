import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mona_sdk",
    version="0.0.58",
    author="MonaLabs",
    author_email="sdk@monalabs.io",
    description="SDK for communicating with Mona's servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/monalabs/mona-sdk",
    download_url="https://pypi.python.org/pypi/mona-sdk/",
    install_requires=[
        "pyjwt",
        "python-jose>=3.2.0",
        "requests-mock>=1.8.0",
        "dataclasses==0.8; python_version<'3.7'",
        "cachetools",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
)

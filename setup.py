import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mona_sdk",
    version="0.0.1",
    author="MonaLabs",
    author_email="anat@monalabs.io",
    description="SDK for communicating with Mona's servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="insert when ready",
    download_url="insert when ready",
    packages=setuptools.find_packages(),
    install_requires=[
        "pyjwt>=1.7.1",
        "python-jose>=3.2.0",
        "requests-mock>=1.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)

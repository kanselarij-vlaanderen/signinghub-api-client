import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="signinghub-api-client",
    version="0.0.1",
    author="Michaël Dierick",
    author_email="michael.dierick@redpencil.io",
    description="Python client for SigningHub's API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "requests-toolbelt",
    ],
    url="https://github.com/kanselarij-vlaanderen/signinghub-api-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

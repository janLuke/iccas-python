#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "pandas",
    "requests",
    "numpy",
    "url-normalize",
    "pyyaml",
    "matplotlib",
    "seaborn",
]

extra_requirements = {
    'cli': ['cloup', 'click', 'tqdm', 'pathvalidate'],
}

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Gianluca Gippetto",
    author_email="gianluca.gippetto@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Helper library for the ICCAS dataset",
    install_requires=requirements,
    extras_require=extra_requirements,
    license="MIT license",
    long_description_content_type="text/x-rst",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="iccas",
    name="iccas",
    packages=find_packages(include=["iccas", "iccas.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/janLuke/iccas-python",
    version="0.1.0",
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'iccas=iccas.__main__:main',
        ],
    },
)

from setuptools import setup

with open("requirements.txt") as f:
    requirements_unfiltered = f.read().splitlines()
    # remove TA-Lib from requirements because it belongs to extras_required
    requirements = [req for req in requirements_unfiltered if "TA-Lib" not in req]

setup(
    name="pinkfish",
    version="2.0.0",
    description="A backtester and spreadsheet library for security analysis.",
    author="Farrell Aultman",
    author_email="fja0568@gmail.com",
    url="https://github.com/fja05680/pinkfish",
    packages=["pinkfish"],
    include_package_data=True,
    license="MIT",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: System :: Distributed Computing",
    ],
    extras_require={
        "talib": ["TA-Lib"],
    },
    data_files=[("", ["requirements.txt"])],
    python_requires=">=3.7",
)

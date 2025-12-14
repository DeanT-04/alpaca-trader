from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="alpaca-trader",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "alpaca-trader=alpaca_trader.cli:main",
        ],
    },
)

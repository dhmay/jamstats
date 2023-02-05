from setuptools import setup, find_packages

setup(
    name='jamstats',
    version='1.0.1',
    description='Data processing, stats and plots on roller derby scoreboard JSON files',
    author='Damon May',
    package_dir={"":"src"},
    include_package_data=True,
    packages=find_packages('src', exclude=['test']),
    scripts=['bin/jamstats'],
    install_requires=['pandas>=1.3.4', 'seaborn>=0.11.2', 'flask>=2.2.2', 'attrdict>=2.0.1', 'gooey>=1.0.8.1'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Source': 'https://github.com/dhmay/jamstats',
    },
)


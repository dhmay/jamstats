from setuptools import setup, find_packages

setup(
    name='jamstats',
    version='0.1.0',    
    description='Data processing, stats and plots on roller derby scoreboard JSON files',
    author='Damon May',
    packages=find_packages('src', exclude=['test']),
    install_requires=['pandas>=1.3.4', 'seaborn>=0.11.2'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Derby afficionados',
        'Programming Language :: Python :: 3',
    ],
)


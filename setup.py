from setuptools import setup, find_packages

setup(
    name='jamstats',
    version='1.1.0',
    description='Data processing, stats and plots on roller derby scoreboard JSON files',
    author='Damon May',
    package_dir={"":"src"},
    include_package_data=True,
    packages=find_packages('src', exclude=['test']),
    scripts=['bin/jamstats'],
    install_requires=['pandas>=1.3.4', 'seaborn>=0.11.2', 'flask>=2.2.2', 'attrdict>=2.0.1', 'gooey>=1.0.8.1', 'websocket-client>=1.2.1',
		      'Flask-SocketIO>=5.3.2', 'python-engineio>=4.3.4', 'gevent>=22.10.2', 'gevent-websocket>=0.10.1'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Source': 'https://github.com/dhmay/jamstats',
    },
)


from setuptools import setup, find_packages

setup(
    name='jamstats-nogui',
    version='1.2.1.4',
    description='Data processing, stats and plots on roller derby scoreboard JSON files. No-GUI version.',
    author='Damon May',
    package_dir={"":"src"},
    include_package_data=True,
    packages=['jamstats'],
    scripts=['bin/jamstats-nogui'],
    install_requires=['pandas>=1.3.4', 'seaborn>=0.11.2', 'flask>=2.2.2', 'attrdict>=2.0.1', 'websocket-client>=1.2.1',
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


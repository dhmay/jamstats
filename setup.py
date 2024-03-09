from setuptools import setup, find_packages

setup(
    name='jamstats',
    version='1.4.9',
    description='Data processing, stats and plots on roller derby scoreboard JSON files',
    author='Damon May',
    package_dir={"":"src"},
    include_package_data=True,
    packages=find_packages('src', exclude=['test']),
    scripts=['bin/jamstats', 'bin/jamstats-nogui'],
    install_requires=['pandas>=2.2.0', 'seaborn>=0.13.2', 'flask>=3.0.2',
                      'eventlet>=0.35.1',
                      'websocket-client>=1.7.0',
		      'Flask-SocketIO>=5.3.6', 'python-engineio>=4.9.0', 'gevent>=24.2.1', 'gevent-websocket>=0.10.1',
		      'dnspython==2.2.1', 'urllib3==1.26.7',
                      'wxpython>=4.2.1', 'gooey>=1.0.8.1',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Source': 'https://github.com/dhmay/jamstats',
    },
    # Next two lines are to make resources available through pip
    package_data = {"": ["src/jamstats/templates/*", "**/jamstats_version.txt"]},
)


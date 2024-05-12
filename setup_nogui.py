from setuptools import setup, find_packages

setup(
    name='jamstats-nogui',
    version='1.4.12',
    description='Data processing, stats and plots on roller derby scoreboard JSON files. No-GUI version.',
    author='Damon May',
    package_dir={"":"src"},
    include_package_data=True,
    packages=['jamstats'],
    scripts=['bin/jamstats-nogui'],
    install_requires=['pandas>=2.2.0', 'seaborn>=0.13.2', 'flask>=3.0.2',
                      'eventlet>=0.35.1',
                      'websocket-client>=1.7.0',
		      'Flask-SocketIO>=5.3.6', 'python-engineio>=4.9.0', 'gevent>=24.2.1', 'gevent-websocket>=0.10.1',
		      'dnspython==2.2.1', 'urllib3==1.26.7',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Source': 'https://github.com/dhmay/jamstats',
    },
)


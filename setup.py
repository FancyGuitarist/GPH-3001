from setuptools import setup
setup(
    name = 'mir',
    version = '1.0.0',
    packages = ['mir'],
    entry_points = {
        'console_scripts': [
            'mir = mir.__main__:main'
        ]
    })

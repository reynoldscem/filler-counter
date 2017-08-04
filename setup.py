from setuptools import setup, find_packages

setup(
    name='filler-counter', version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'filler-counter=filler_counter.filler_counter:main'
        ]
    }
)

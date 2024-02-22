from setuptools import setup

setup(
        name='ztmAPI448474',
        version='0.1',
        description='Fetch and analize Warsaw ztm API data',
        packages=['ztmAPI448474'],
        install_requires=[
            'requests',
            'numpy',
            'pandas',
            'folium',
            'matplotlib'
        ],
        author_email='wr448474@students.mimuw.edu.pl',
        url='https://github.com/kiwitrr2944/analizaAutobusowa',
        zip_safe=False
)

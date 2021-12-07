from setuptools import setup, find_packages

setup(
    name='tripper',
    version='0.0.1',
    packages=find_packages(include=['tripper', 'tripper.*']),
    include_package_data=True,
    author='Stefan Heid',
    author_email='stefan.heid@upb.de',
    description='Download utility to create and maintain local collection of Tatort Episodes published in the D,A,CH - mediathek',
    long_description=open('README.rst').read(),
    entry_points={'console_scripts': [
        'tripper = tripper.cli:main ',
    ]},
    license='GPLv3',
    keywords='tatort,mediathek,ripper',
    url='https://github.com/stheid/tripper',
    install_requires=[
        'click',
        'pandas',
        'thefuzz',
        'requests',
        'pyyaml'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: POSIX :: Linux',
        'Framework :: Sphinx'
    ]
)

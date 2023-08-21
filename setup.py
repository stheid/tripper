from setuptools import setup, find_packages

setup(
    name='tripper',
    version='0.1.17',
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
    install_requires=['click', 'tqdm', 'pyyaml',
                      'pandas', 'lxml',
                      'thefuzz', 'python-levenshtein',
                      'requests', 'youtube-dl'
                      ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.8',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Framework :: Sphinx'
    ]
)

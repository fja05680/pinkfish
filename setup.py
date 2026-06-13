from setuptools import find_packages, setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pinkfish',
    version='2.3.0',
    description='A backtester and spreadsheet library for security analysis.',
    author='Farrell Aultman',
    author_email='fja0568@gmail.com',
    url='https://github.com/fja05680/pinkfish',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: System :: Distributed Computing',
    ],
    extras_require={
        'talib':  ['TA-Lib'],
    },
    data_files=[('', ['requirements.txt'])],
    python_requires=">=3.11",
)

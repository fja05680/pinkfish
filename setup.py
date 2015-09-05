from setuptools import setup

setup(
    name='pinkfish',
    version='0.5.1',
    description='A backtester and spreadsheet library for security analysis.',
    author='Farrell Aultman',
    author_email='fja0568@gmail.com',
    url='http://github.com/fja0568/pinkfish',
    packages=['pinkfish'],
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: System :: Distributed Computing',
    ],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
    ],
    extras_require={
        'talib':  ["talib"],
        'itable':  ["itable"],
    }
)

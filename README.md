pinkfish
======

**11-12-2019: prettier_graphs (see double-7s example)** 
**11-01-2019: Add monthly and holding_period tables (see buy-and-hold example)**  
**07-31-2019: First major update since original release - Add scale-in and scale-out capability**

A backtester and spreadsheet library for security analysis.

Why another python backtesting library?  How is pinkfish different?
Simple, I couldn't find a python backtesting library that allowed me to backtest intraday strategies with daily data.  Even simple strategies like 'buying on the close' on the SAME day a 'new 20 day high is set' were not allowed.  Additionally, I was put off by the complexity of some of the libraries available, and wanted something simple, that doesn't get in the way, and just allows me to test my trading ideas.  I didn't set out to write a new backtesting library, but I had to.  Daily data is free; minute and tick data are typically not.  Using minute and tick data can require hours to run vs seconds for daily data.

Some of the key features of pinkfish:
 - leverages pandas for dataframe, spreadsheet like features
 - leverages matplotlib for making financial graphs
 - uses ta-lib to easily implement technical indicators
 - uses daily data (vs minute or tick data) for intraday trading
 - uses free daily data from yahoo finance
 - simple to use python API
 - create spreadsheets within Jupyter Notebook by utilizing pandas dataframes and itable formatting

## Installation
Follow the installation instructions located at:
https://fja05680.github.io/pinkfish/

## Examples
 - [spreadsheet](https://fja05680.github.io/pinkfish/examples/spreadsheet.html) - make a read only spreadsheet within ipython
 - [golden-cross](http://fja05680.github.io/pinkfish/examples/golden-cross.html) - an example illustrating the classic long term trading algorithm

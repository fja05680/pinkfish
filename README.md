pinkfish
======     

ANNOUNCEMENT: I refreshed all of the examples to make them simplier and more consistent with each other.  They are also roughly ordered by complexity beginning with the easiest.  I'll be adding some additional examples over the coming days.  I added a TODO file that shows what else is planned for pinkfish.

A backtester and spreadsheet library for security analysis.

Why another python backtesting library?  How is pinkfish different?
Simple, I couldn't find a python backtesting library that allowed me to backtest intraday strategies with daily data.  Even simple strategies like 'buying on the close' on the SAME day a 'new 20 day high is set' were not allowed.  Additionally, I was put off by the complexity of some of the libraries available, and wanted something simple, that doesn't get in the way, and just allows me to test my trading ideas.  One user commented that Pinkfish is "very lightweight and to the point".  I didn't set out to write a new backtesting library, but I had to.  Daily data is free; minute and tick data are typically not.  Using minute and tick data can require hours to run vs seconds for daily data.

Some of the key features of pinkfish:
 - leverages pandas for dataframe, spreadsheet like features
 - leverages matplotlib for making financial graphs
 - uses ta-lib to easily implement technical indicators
 - uses daily data (vs minute or tick data) for intraday trading
 - uses free daily data from yahoo finance
 - simple to use python API
 - backtest single stock/ETF strategy or a portolio (basket of stocks/ETFs)
 - backtest short selling strategies and simulate trading with margin
 - write optimizers to select the best parameters
 - create spreadsheets within Jupyter Notebook by utilizing pandas dataframes and itable formatting

## Installation
Follow the installation instructions located at:
https://fja05680.github.io/pinkfish/

## Examples
 - [buy-and-hold](https://fja05680.github.io/pinkfish/examples/buy-and-hold.html) - basic buy and hold strategy
 - [golden-cross](http://fja05680.github.io/pinkfish/examples/golden-cross.html) - classic long term trading algorithm
 - [spreadsheet](https://fja05680.github.io/pinkfish/examples/spreadsheet.html) - read only spreadsheet within jupyter notebook
 - [momentum-gem](http://fja05680.github.io/pinkfish/examples/momentum-gem.html) - Gary Antonacci’s Dual Momentum strategy
 
## Documentation
The pinkfish API documentation:
https://fja05680.github.io/pinkfish/docs/html/pinkfish/index.html

## Pinkfish on youtube
https://www.youtube.com/channel/UCsPHH2UBn8Fz0g0MGrZ2Ihw

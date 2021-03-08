pinkfish
======     

ANNOUNCEMENT: I now have a youtube channel dedicated to Pinkfish.  First 4 videos already uploaded.  I'll try t post a new video every week.  Open to recommendations for video content.

https://www.youtube.com/channel/UCsPHH2UBn8Fz0g0MGrZ2Ihw


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
 
 **IMPORTANT 08-25-2020: Pinkfish v1.0.0**  
In case anyone has noticed...  there has been a flury of development on Pinkfish over this past year.  I first started Pinkfish over 5 years ago and initially all it could do was single long stock backtest and analysis.  Now it's capable of portfolio, short selling, and margin.  I've also added custom indicators, more statistics, and lots of analysis tools.  It now does pretty much everything you'd want for stocks on a daily timeframe.  That's why I have decided to offically stamp Pinkfish as v1.0.0.  (I will use semantic versioning.)  Eventually, I may add other timeframes and futures.  But now, I'm hitting the pause button and working on my personal investment strategies.  I'm glad that I built this tool.  It's helped me understand systematic trading much better.  In the near future, I plan to set up a youtube channel to demonstrate how to install and use Pinkish.  I feel this would be far more effective than documentation.  Stay tuned...

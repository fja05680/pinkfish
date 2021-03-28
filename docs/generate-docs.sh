# from pinkfish/docs

# remove old html
rm html -fr

# generate html
pdoc --html ../../pinkfish/

# generate markdown extra
pdoc --pdf ../../pinkfish/ > pinkfish.txt

# generate pdf from markdown extra
pandoc --pdf-engine=xelatex pinkfish.txt -o pinkfish.pdf

echo Done.

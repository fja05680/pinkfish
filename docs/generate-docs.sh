# from pinkfish/docs

# remove old html
rm html -fr

# generate html (repo root must be on PYTHONPATH)
export PYTHONPATH="$(cd .. && pwd)"
pdoc --html pinkfish

echo Done.

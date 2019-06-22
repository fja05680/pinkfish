
call "./env/Scripts/activate"
py.test --cov-report html --cov --doctest-modules --cache-clear --ignore=examples

pause
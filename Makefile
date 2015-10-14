# Author: Jean-Michel Begon

all: clean inplace test

clean:
	python setup.py clean

in: inplace

inplace:
	python setup.py build_ext --inplace

test:
	nosetests clustertools

doc: inplace
	$(MAKE) -C doc html

clean-doc:
	rm -rf doc/_build
	rm -rf doc/generated

view-doc: doc
	open doc/_build/html/index.html

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-cms-anchor-plugins",
    version = "0.0.1",
    url = "http://github.com/andyrooger/Django-cms-Anchor-Plugins",
    license = "GPL",
    description = "django-cms plugins for anchor functionality",
    long_description = read('README.markdown'),
    author = "Andy Gurden",
    author_email = "as.gurden@gmail.com",
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False
)

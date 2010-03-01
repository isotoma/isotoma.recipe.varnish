from setuptools import setup, find_packages

version = '0.0.0'

setup(
    name = 'isotoma.recipe.varnish',
    version = version,
    description = "Set up varnish and varnish logging",
    long_description = open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
    classifiers = [
        "Framework :: Buildout",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Apache Software License",

    ],
    keywords = "varnish proxy cache buildout",
    author = "Doug Winter",
    author_email = "doug.winter@isotoma.com",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    namespace_packages = ['isotoma', 'isotoma.recipe'],
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'zc.buildout',
        'Cheetah',
    ],
    entry_points = {
        "zc.buildout": [
            "default = isotoma.recipe.varnish:Varnish",
        ],
    }
)

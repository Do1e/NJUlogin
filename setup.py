import setuptools
import NJUlogin

with open("README.md", "r", encoding='utf-8') as fp:
    long_description = fp.read()

setuptools.setup(
    name = NJUlogin.__title__,
    version = NJUlogin.__version__,
    author = NJUlogin.__author__,
    author_email = NJUlogin.__author_email__,
    description = NJUlogin.__description__,
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = NJUlogin.__url__,
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = ['requests', 'opencv-python-headless',
        'numpy', 'lxml', 'ddddocr', 'pycryptodome',
        'inputimeout', 'user_agents'],
    python_requires = '>=3'
)

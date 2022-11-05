import setuptools

with open("README.md", "r", encoding='utf-8') as fp:
    long_description = fp.read()

setuptools.setup(
    name="NJUlogin",
    version="2.0",
    author="Do1e",
    author_email="dpj.email@qq.com",
    description="南京大学统一身份认证登录模块，可用于登录校园各种网站",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Do1e/NJUlogin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests', 'opencv-python',
        'numpy', 'lxml', 'ddddocr', 'pycryptodome',
        'inputimeout'],
    python_requires='>=3'
)

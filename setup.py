import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unleash-client",
    version="3.6.0",
    author="pvz301",
    author_email="parvez.alam@haptik.co",
    description="Client for unleash server",
    long_description=long_description,
    url="https://github.com/hellohaptik/unleash-python-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()


required = ["pyzmq", "cloudpickle"]

setup(
    name="tasq",
    version="1.3.0",
    description="Distributed task queue using ZMQ, cloudpickle, and actor-based workers",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "static"]),
    install_requires=required,
    scripts=["tq"],
    test_suite="tests",
    python_requires=">=3.14",
)

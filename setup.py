import setuptools
from ProkaryoteAssembly.config import __email__, __author__, __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

# TODO: Improve this setup by using the layout used in SeqPresenceAbsence
setuptools.setup(
    name="ProkaryoteAssembly",
    install_requires=['click'],
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="Internal BFSSI package for assembling prokaryotic genomes from short reads",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bfssi-forest-dussault/ProkaryoteAssembly",
    packages=setuptools.find_packages(),
    scripts=['ProkaryoteAssembly/prokaryote_assemble.py', 'ProkaryoteAssembly/prokaryote_assemble_dir.py']
)

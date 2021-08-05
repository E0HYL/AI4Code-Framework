from distutils.core import setup

_dependencies = [
    'cycler==0.10.0',
    'kiwisolver==1.0.1',
    'matplotlib==2.2.3',
    'numpy==1.15.1',
    'pyparsing==2.2.0',
    'python-dateutil==2.7.3',
    'pytz==2018.5',
    'scikit-learn==0.19.2',
    'scipy==1.1.0',
    'six==1.11.0',
    'tqdm==4.25.0']

setup(
    name='Tesseract',
    version='0.9',
    description='Tesseract: A library for performing '
                'time-aware classifications.',
    maintainer='Feargus Pendlebury',
    maintainer_email='Feargus.Pendlebury[at]rhul.ac.uk',
    url='',
    packages=['tesseract'],
    setup_requires=_dependencies,
    install_requires=_dependencies
)

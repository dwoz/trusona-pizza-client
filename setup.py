from setuptools import setup

setup(
    name = 'trusona-pizza-client',
    packages = ['pizza_client'],
    entry_points = {
        'console_scripts': ['pizza-client=pizza_client.app:main'],
    },
    version = '0.0.2',
    description = (
        'An implimentation of the Trusona pizza client'
    ),
    author = 'Daniel Wozniak',
    author_email = 'dan@woz.io',
    url = 'https://github.com/dwoz/trusona-pizza-client',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
)

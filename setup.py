# setup.py
from setuptools import setup

plugin_identifier = "ntfy"
plugin_package = "octoprint_ntfy"
plugin_name = "OctoPrint-Ntfy"
plugin_version = "0.1.4"
plugin_description = "Integration with self-hosted ntfy"
plugin_author = "Tip-Topych"
plugin_author_email = "your@email.com"
plugin_url = "https://github.com/Tip-Topych/OctoPrint-Ntfy"
plugin_license = "AGPLv3"

plugin_requires = ["requests", "eventlet"]

plugin_additional_data = [] # MANIFEST.in handles templates now

setup_parameters = dict(
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    packages=[plugin_package],
    include_package_data=True, # Важно для MANIFEST.in
    zip_safe=False,
    install_requires=plugin_requires,
    entry_points={
        "octoprint.plugin": [
            "ntfy = octoprint_ntfy"
        ]
    },
)

if __name__ == "__main__":
    setup(**setup_parameters)
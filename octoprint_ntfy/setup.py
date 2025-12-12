# setup.py
plugin_identifier = "ntfy"
plugin_package = "octoprint_ntfy"
plugin_name = "OctoPrint-Ntfy"
plugin_version = "0.1.0"
plugin_description = "Отправляет уведомления и скриншоты в self-hosted ntfy"
plugin_author = "Ваше Имя"
plugin_author_email = "your@email.com"
plugin_url = "https://github.com/yourusername/OctoPrint-Ntfy"
plugin_license = "AGPLv3"

from setuptools import setup

def plugin_data(pkg, *dirs):
    import os
    data = []
    for d in dirs:
        for walk in os.walk(os.path.join(pkg, d)):
            data.append(walk[0][len(pkg) + 1 :] + "/*")
    return data

setup_parameters = dict(
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    packages=[plugin_package],
    package_data={plugin_package: plugin_data(plugin_package, "templates")},
    include_package_data=True,
    zip_safe=False,
    install_requires=["requests"],  # Нам нужна эта библиотека
    entry_points={
        "octoprint.plugin": [
            "ntfy = octoprint_ntfy"
        ]
    },
)

if __name__ == "__main__":
    setup(**setup_parameters)
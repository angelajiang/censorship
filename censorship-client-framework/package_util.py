"""
Some utilities for working with packages.
These should not have to be modified.
"""
import os
import re


def parse_version(version_string):
    version = [int(x) for x in version_string.split(".")]
    while version and version[-1] == 0:
        version.pop()
    return tuple(version)


def format_version(version):
    return ".".join([str(x) for x in version])


_egg_regex = re.compile(r'(?P<package>[a-zA-Z0-9_]+)-(?P<version>[0-9\.]+)-py(?P<py>[0-9\.]+)(-(?P<platform>[^\.]+))?\.egg$')


def parse_egg_name(fname):
    m = _egg_regex.match(fname)
    if m:
        d = m.groupdict()
        d["version"] = parse_version(d["version"])
        d["py"] = parse_version(d["py"])

        return d
    return None


def find_eggs(path):
    eggs = {}

    # get all the package/version combinations available
    # in the package directory
    for root, dirs, files in os.walk(path):
        for f in files:
            egg = parse_egg_name(f)
            if egg is None: continue

            full_path = os.path.join(root, f)

            package = eggs.setdefault(egg["package"], {})
            versions = package.setdefault(egg["version"], [])
            versions.append(full_path)
    
    return eggs


def choose_eggs(path, blacklist):
    eggs = find_eggs(path)

    chosen = {}

    # choose the latest version for each package
    for package in eggs:
        versions = eggs[package]
        # filter versions that are blacklisted
        ok_versions = {version:paths for (version, paths) in versions.iteritems() if (package, version) not in blacklist}
        if not ok_versions:
            # fall back to the oldest version, even if it has been blacklisted
            min_version = min(versions)
            ok_versions = {min_version:versions[min_version]}
        latest = max(ok_versions)
        path = ok_versions[latest][0]

        chosen[package] = latest, path

    return chosen


class Blacklist(object):
    """ Provides interface for blacklisting package/version combinations
    """

    def __init__(self, config):
        self.config = config

    def config(self):
        return self.config

    def get(self):
        bl = set() # set of (package name, version) that are blacklisted
        c = self.config
        if not c.has_section("blacklist"): return set()

        for package, versions in c.items("blacklist"):
            versions = [parse_version(x.strip()) for x in versions.split(",") if x.strip()]
            for version in versions:
                bl.add( (package, version) )

        return bl

    def blacklisted(self, package, version):
        return (package, version) in self.get()

    def add(self, package, version):
        if not self.config.has_section("blacklist"):
            self.config.add_section("blacklist")
        if not self.config.has_option("blacklist", package):
            self.config.set("blacklist", package, format_version(version))
        else:
            versions = self.config.get("blacklist", package)
            versions = set([parse_version(x.strip()) for x in versions.split(",") if x.strip()])
            versions.add(version)
            version_text = ", ".join([format_version(x) for x in sorted(versions)])
            self.config.set("blacklist", package, version_text)

    def remove(self, package, version):
        if not self.config.has_section("blacklist"):
            return
        if self.config.has_option("blacklist", package):
            versions = self.config.get("blacklist", package)
            versions = set([parse_version(x.strip()) for x in versions.split(",") if x.strip()])
            versions.discard(version)
            if not versions:
                self.config.remove_option("blacklist", package)
            else:
                version_text = ", ".join([format_version(x) for x in sorted(versions)])
                self.config.set("blacklist", package, version_text)

    def clear(self):
        if self.config.has_section("blacklist"):
            self.config.remove_section("blacklist")

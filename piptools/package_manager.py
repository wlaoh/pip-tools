import operator
from functools import partial
from version import NormalizedVersion  # PEP386 compatible version numbers
from datastructures import Spec


class NoPackageMatch(Exception):
    pass


class BasePackageManager(object):
    def find_best_match(self, spec):
        raise NotImplementedError('Implement this in a subclass.')

    def get_dependencies(self, name, version):
        raise NotImplementedError('Implement this in a subclass.')


class FakePackageManager(BasePackageManager):
    def __init__(self, fake_contents):
        """Creates a fake package manager index, for easy testing.  The
        fake_contents argument is a dictionary containing 'name-version' keys
        and lists-of-specs values.

        Example:

            {
                'foo-0.1': ['bar', 'qux'],
                'bar-0.2': ['qux>0.1'],
                'qux-0.1': [],
                'qux-0.2': [],
            }
        """
        # Sanity check (parsing will return errors if content is wrongly
        # formatted)
        for pkg_key, list_of_specs in fake_contents.items():
            try:
                _, _ = self.parse_package_key(pkg_key)
            except ValueError:
                raise ValueError('Invalid index entry: %s' % (pkg_key,))
            assert isinstance(list_of_specs, list)

        self._contents = fake_contents

    def parse_package_key(self, pkg_key):
        try:
            return pkg_key.rsplit('-', 1)
        except ValueError:
            raise ValueError('Invalid package key: %s (required format: "name-version")' % (pkg_key,))

    def iter_package_versions(self):
        """Iters over all package versions, returning key-value pairs."""
        for key in self._contents:
            yield self.parse_package_key(key)

    def iter_versions(self, given_name):
        """Will return all versions available for the current package name."""
        for name, version in self.iter_package_versions():
            if name == given_name:
                yield version

    def matches_qual(self, version, qual, value):
        """Returns whether version matches the qualifier and the given value."""
        ops = {
            '==': operator.eq,
            '<': operator.lt,
            '>': operator.gt,
            '<=': operator.le,
            '>=': operator.ge,
        }
        return ops[qual](NormalizedVersion(version), NormalizedVersion(value))

    def pick_highest(self, list_of_versions):
        """Picks the highest version from a list, according to PEP386 logic."""
        return str(max(map(NormalizedVersion, list_of_versions)))

    def find_best_match(self, spec):
        """This requires a bit of reverse engineering of PyPI's logic that
        finds a pacakge for a given spec, but it's not too hard.
        """
        versions = list(self.iter_versions(spec.name))
        for qual, value in spec.preds:
            pred = partial(self.matches_qual, qual=qual, value=value)
            versions = filter(pred, versions)
        if len(versions) == 0:
            raise NoPackageMatch('No package found for %s' % (spec,))
        return self.pick_highest(versions)

    def get_dependencies(self, name, version):
        pkg_key = '%s-%s' % (name, version)
        specs = []
        for specline in self._contents[pkg_key]:
            specs.append(Spec.from_line(specline))
        return specs


class PackageManager(BasePackageManager):
    """The default package manager that goes to PyPI and caches locally."""
    pass


if __name__ == '__main__':
    pass
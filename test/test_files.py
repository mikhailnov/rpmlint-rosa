import pytest
from rpmlint.checks.FilesCheck import FilesCheck
from rpmlint.checks.FilesCheck import pyc_magic_from_chunk, pyc_mtime_from_chunk
from rpmlint.checks.FilesCheck import python_bytecode_to_script as pbts
from rpmlint.checks.FilesCheck import script_interpreter as se
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, get_tested_path


@pytest.fixture(scope='function', autouse=True)
def filescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FilesCheck(CONFIG, output)
    return output, test


def test_pep3147():
    assert pbts('/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyc') == '/usr/lib64/python3.4/__phello__.foo.py'
    assert pbts('/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyo') == '/usr/lib64/python3.4/__phello__.foo.py'


def test_py2():
    assert pbts('/usr/lib/python2.7/site-packages/_pytest/main.pyc') == '/usr/lib/python2.7/site-packages/_pytest/main.py'
    assert pbts('/usr/lib/python2.7/site-packages/_pytest/main.pyo') == '/usr/lib/python2.7/site-packages/_pytest/main.py'


def test_pep0488():
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-1.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-2.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'


def chunk_from_pyc(version, size=16):
    """Helper to get start of an example pyc file as bytes"""
    path = get_tested_path('pyc/__future__.cpython-{}.pyc'.format(version))
    with open(path, 'rb') as f:
        return f.read(size)


@pytest.mark.parametrize('package', ['binary/python3-power'])
def test_python_bytecode_magic(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    assert not output.results
    out = output.print_results(output.results)
    assert 'python-bytecode-wrong-magic-value' not in out


@pytest.mark.parametrize('version, magic', ((36, 3379), (37, 3393)))
def test_pyc_magic_from_chunk(version, magic):
    chunk = chunk_from_pyc(version)
    assert pyc_magic_from_chunk(chunk) == magic


@pytest.mark.parametrize('version, mtime', ((36, 1513659236), (37, 1519778958)))
def test_pyc_mtime_from_chunk(version, mtime):
    chunk = chunk_from_pyc(version)
    assert pyc_mtime_from_chunk(chunk) == mtime


@pytest.mark.parametrize('package', ['binary/netmask-debugsource'])
def test_devel_files(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 5
    out = output.print_results(output.results)
    assert 'devel-file-in-non-devel-package' not in out
    assert 'incorrect-fsf-address' in out
    assert 'no-documentation' in out


def test_script_interpreter():
    assert se(b'#!/bin/sh\n# Hello world!\n') == ('/bin/sh', '')
    assert se(b'#!/bin/bash -e\n') == ('/bin/bash', '-e')
    assert se(b'#! /usr/bin/perl -wT \n') == ('/usr/bin/perl', '-wT')
    assert se(b'#!/usr/bin/env python3 foo') == ('/usr/bin/env', 'python3 foo')
    assert se(b'# something here\n#!not a shebang') == (None, '')


def test_scm_regex():
    from rpmlint.checks.FilesCheck import scm_regex

    assert scm_regex.search('/foo/CVS/bar')
    assert scm_regex.search('/foo/RCS/bar')
    assert scm_regex.search('/bar/foo,v')
    assert scm_regex.search('bar/.svnignore')
    assert scm_regex.search('bar/.git/refs')


def test_lib_regex():
    from rpmlint.checks.FilesCheck import lib_regex

    # true matches
    assert all(
        lib_regex.search(x) for x in
        ('/lib/libnsl-2.26.so',
         '/usr/lib64/libgnomeui.so.3',
         '/lib64/libgcc_s.so.1'))

    # false positives
    assert not any(
        lib_regex.search(x) for x in
        ('/usr/share/gdb/auto-load/usr/lib/libglib-2.0.so.0.4600.1-gdb.py',
         '/usr/share/doc/findlib/lib-1.0.so',
         '/usr/lib64/libvulkan_radeon.so',
         '/usr/lib64/rsocket/binary',))

# -*- coding: utf-8 -*-
"""Tests string formatting functions."""
import curses
import mock


def test_parameterizing_string_args_unspecified(monkeypatch):
    """Test default args of formatters.ParameterizingString."""
    from blessed.formatters import ParameterizingString, FormattingString
    # first argument to tparm() is the sequence name, returned as-is;
    # subsequent arguments are usually Integers.
    tparm = lambda *args: u'~'.join(
        arg.decode('latin1') if not num else '%s' % (arg,)
        for num, arg in enumerate(args)).encode('latin1')

    monkeypatch.setattr(curses, 'tparm', tparm)

    # given,
    pstr = ParameterizingString(u'')

    # excersize __new__
    assert str(pstr) == u''
    assert pstr._normal == u''
    assert pstr._name == u'<not specified>'

    # excersize __call__
    zero = pstr(0)
    assert type(zero) is FormattingString
    assert zero == u'~0'
    assert zero('text') == u'~0text'

    # excersize __call__ with multiple args
    onetwo = pstr(1, 2)
    assert type(onetwo) is FormattingString
    assert onetwo == u'~1~2'
    assert onetwo('text') == u'~1~2text'


def test_parameterizing_string_args(monkeypatch):
    """Test basic formatters.ParameterizingString."""
    from blessed.formatters import ParameterizingString, FormattingString

    # first argument to tparm() is the sequence name, returned as-is;
    # subsequent arguments are usually Integers.
    tparm = lambda *args: u'~'.join(
        arg.decode('latin1') if not num else '%s' % (arg,)
        for num, arg in enumerate(args)).encode('latin1')

    monkeypatch.setattr(curses, 'tparm', tparm)

    # given,
    pstr = ParameterizingString(u'cap', u'norm', u'seq-name')

    # excersize __new__
    assert str(pstr) == u'cap'
    assert pstr._normal == u'norm'
    assert pstr._name == u'seq-name'

    # excersize __call__
    zero = pstr(0)
    assert type(zero) is FormattingString
    assert zero == u'cap~0'
    assert zero('text') == u'cap~0textnorm'

    # excersize __call__ with multiple args
    onetwo = pstr(1, 2)
    assert type(onetwo) is FormattingString
    assert onetwo == u'cap~1~2'
    assert onetwo('text') == u'cap~1~2textnorm'


def test_parameterizing_string_type_error(monkeypatch):
    """Test formatters.ParameterizingString raising TypeError"""
    from blessed.formatters import ParameterizingString

    def tparm_raises_TypeError(*args):
        raise TypeError('custom_err')

    monkeypatch.setattr(curses, 'tparm', tparm_raises_TypeError)

    # given,
    pstr = ParameterizingString(u'cap', u'norm', u'cap-name')

    # ensure TypeError when given a string raises custom exception
    try:
        pstr('XYZ')
        assert False, "previous call should have raised TypeError"
    except TypeError, err:
        assert (err.args[0] == (  # py3x
            "A native or nonexistent capability template, "
            "'cap-name' received invalid argument ('XYZ',): "
            "custom_err. You probably misspelled a "
            "formatting call like `bright_red'") or
            err.args[0] == (
                "A native or nonexistent capability template, "
                "u'cap-name' received invalid argument ('XYZ',): "
                "custom_err. You probably misspelled a "
                "formatting call like `bright_red'"))

    # ensure TypeError when given an integer raises its natural exception
    try:
        pstr(0)
        assert False, "previous call should have raised TypeError"
    except TypeError, err:
        assert err.args[0] == "custom_err"


def test_formattingstring(monkeypatch):
    """Test formatters.FormattingString"""
    from blessed.formatters import (FormattingString)

    # given, with arg
    pstr = FormattingString(u'attr', u'norm')

    # excersize __call__,
    assert pstr._normal == u'norm'
    assert str(pstr) == u'attr'
    assert pstr('text') == u'attrtextnorm'

    # given, without arg
    pstr = FormattingString(u'', u'norm')
    assert pstr('text') == u'text'


def test_nullcallablestring(monkeypatch):
    """Test formatters.NullCallableString"""
    from blessed.formatters import (NullCallableString)

    # given, with arg
    pstr = NullCallableString()

    # excersize __call__,
    assert str(pstr) == u''
    assert pstr('text') == u'text'
    assert pstr('text', 1) == u''
    assert pstr('text', 'moretext') == u''
    assert pstr(99, 1) == u''
    assert pstr() == u''
    assert pstr(0) == u''


def test_split_compound():
    """Test formatters.split_compound."""
    from blessed.formatters import split_compound

    assert split_compound(u'') == [u'']
    assert split_compound(u'a_b_c') == [u'a', u'b', u'c']
    assert split_compound(u'a_on_b_c') == [u'a', u'on_b', u'c']
    assert split_compound(u'a_bright_b_c') == [u'a', u'bright_b', u'c']
    assert split_compound(u'a_on_bright_b_c') == [u'a', u'on_bright_b', u'c']


def test_resolve_capability(monkeypatch):
    """Test formatters.resolve_capability and term sugaring """
    from blessed.formatters import resolve_capability

    # given, always returns a b'seq'
    tigetstr = lambda attr: ('seq-%s' % (attr,)).encode('latin1')
    monkeypatch.setattr(curses, 'tigetstr', tigetstr)
    term = mock.Mock()
    term._sugar = dict(mnemonic='xyz')

    # excersize
    assert resolve_capability(term, 'mnemonic') == u'seq-xyz'
    assert resolve_capability(term, 'natural') == u'seq-natural'

    # given, where tigetstr returns None
    tigetstr_none = lambda attr: None
    monkeypatch.setattr(curses, 'tigetstr', tigetstr_none)

    # excersize,
    assert resolve_capability(term, 'natural') == u''

    # given, where does_styling is False
    def raises_exception(*args):
        assert False, "Should not be called"
    term.does_styling = False
    monkeypatch.setattr(curses, 'tigetstr', raises_exception)

    # excersize,
    assert resolve_capability(term, 'natural') == u''


def test_resolve_color(monkeypatch):
    """Test formatters.resolve_color."""
    from blessed.formatters import (resolve_color,
                                    FormattingString,
                                    NullCallableString)

    color_cap = lambda digit: 'seq-%s' % (digit,)
    monkeypatch.setattr(curses, 'COLOR_RED', 1984)

    # given, terminal with color capabilities
    term = mock.Mock()
    term._background_color = color_cap
    term._foreground_color = color_cap
    term.number_of_colors = -1
    term.normal = 'seq-normal'

    # excersize,
    red = resolve_color(term, 'red')
    assert type(red) == FormattingString
    assert red == u'seq-1984'
    assert red('text') == u'seq-1984textseq-normal'

    # excersize bold, +8
    bright_red = resolve_color(term, 'bright_red')
    assert type(bright_red) == FormattingString
    assert bright_red == u'seq-1992'
    assert bright_red('text') == u'seq-1992textseq-normal'

    # given, terminal without color
    term.number_of_colors = 0

    # excersize,
    red = resolve_color(term, 'red')
    assert type(red) == NullCallableString
    assert red == u''
    assert red('text') == u'text'

    # excesize bold,
    bright_red = resolve_color(term, 'bright_red')
    assert type(bright_red) == NullCallableString
    assert bright_red == u''
    assert bright_red('text') == u'text'


def test_resolve_attribute_as_color(monkeypatch):
    """ Test simple resolve_attribte() given color name. """
    import blessed
    from blessed.formatters import resolve_attribute

    resolve_color = lambda term, digit: 'seq-%s' % (digit,)
    COLORS = set(['COLORX', 'COLORY'])
    COMPOUNDABLES = set(['JOINT', 'COMPOUND'])
    monkeypatch.setattr(blessed.formatters, 'resolve_color', resolve_color)
    monkeypatch.setattr(blessed.formatters, 'COLORS', COLORS)
    monkeypatch.setattr(blessed.formatters, 'COMPOUNDABLES', COMPOUNDABLES)
    term = mock.Mock()
    assert resolve_attribute(term, 'COLORX') == u'seq-COLORX'


def test_resolve_attribute_as_compoundable(monkeypatch):
    """ Test simple resolve_attribte() given a compoundable. """
    import blessed
    from blessed.formatters import resolve_attribute, FormattingString

    resolve_cap = lambda term, digit: 'seq-%s' % (digit,)
    COMPOUNDABLES = set(['JOINT', 'COMPOUND'])
    monkeypatch.setattr(blessed.formatters, 'resolve_capability', resolve_cap)
    monkeypatch.setattr(blessed.formatters, 'COMPOUNDABLES', COMPOUNDABLES)
    term = mock.Mock()
    term.normal = 'seq-normal'

    compound = resolve_attribute(term, 'JOINT')
    assert type(compound) is FormattingString
    assert str(compound) == u'seq-JOINT'
    assert compound('text') == u'seq-JOINTtextseq-normal'


def test_resolve_attribute_non_compoundables(monkeypatch):
    """ Test recursive compounding of resolve_attribute(). """
    import blessed
    from blessed.formatters import resolve_attribute, ParameterizingString
    uncompoundables = lambda attr: ['split', 'compound']
    resolve_cap = lambda term, digit: 'seq-%s' % (digit,)
    monkeypatch.setattr(blessed.formatters, 'split_compound', uncompoundables)
    monkeypatch.setattr(blessed.formatters, 'resolve_capability', resolve_cap)
    tparm = lambda *args: u'~'.join(
        arg.decode('latin1') if not num else '%s' % (arg,)
        for num, arg in enumerate(args)).encode('latin1')
    monkeypatch.setattr(curses, 'tparm', tparm)

    term = mock.Mock()
    term.normal = 'seq-normal'

    # given
    pstr = resolve_attribute(term, 'not-a-compoundable')
    assert type(pstr) == ParameterizingString
    assert str(pstr) == u'seq-not-a-compoundable'
    # this is like calling term.move_x(3)
    assert pstr(3) == u'seq-not-a-compoundable~3'
    # this is like calling term.move_x(3)('text')
    assert pstr(3)('text') == u'seq-not-a-compoundable~3textseq-normal'


def test_resolve_attribute_recursive_compoundables(monkeypatch):
    """ Test recursive compounding of resolve_attribute(). """
    import blessed
    from blessed.formatters import resolve_attribute, FormattingString

    # patch,
    resolve_cap = lambda term, digit: 'seq-%s' % (digit,)
    monkeypatch.setattr(blessed.formatters, 'resolve_capability', resolve_cap)
    tparm = lambda *args: u'~'.join(
        arg.decode('latin1') if not num else '%s' % (arg,)
        for num, arg in enumerate(args)).encode('latin1')
    monkeypatch.setattr(curses, 'tparm', tparm)
    monkeypatch.setattr(curses, 'COLOR_RED', 6502)
    monkeypatch.setattr(curses, 'COLOR_BLUE', 6800)

    color_cap = lambda digit: 'seq-%s' % (digit,)
    term = mock.Mock()
    term._background_color = color_cap
    term._foreground_color = color_cap
    term.normal = 'seq-normal'

    # given,
    pstr = resolve_attribute(term, 'bright_blue_on_red')

    # excersize,
    assert type(pstr) == FormattingString
    assert str(pstr) == 'seq-6808seq-6502'
    assert pstr('text') == 'seq-6808seq-6502textseq-normal'


def test_pickled_parameterizing_string(monkeypatch):
    """Test pickle-ability of a formatters.ParameterizingString."""
    from blessed.formatters import ParameterizingString, FormattingString

    # simply send()/recv() over multiprocessing Pipe, a simple
    # pickle.loads(dumps(...)) did not reproduce this issue,
    from multiprocessing import Pipe
    import pickle

    # first argument to tparm() is the sequence name, returned as-is;
    # subsequent arguments are usually Integers.
    tparm = lambda *args: u'~'.join(
        arg.decode('latin1') if not num else '%s' % (arg,)
        for num, arg in enumerate(args)).encode('latin1')

    monkeypatch.setattr(curses, 'tparm', tparm)

    # given,
    pstr = ParameterizingString(u'seqname', u'norm', u'cap-name')

    # multiprocessing Pipe implicitly pickles.
    r, w = Pipe()

    # excersize picklability of ParameterizingString
    for proto_num in range(pickle.HIGHEST_PROTOCOL):
        assert pstr == pickle.loads(pickle.dumps(pstr, protocol=proto_num))
    w.send(pstr)
    r.recv() == pstr

    # excersize picklability of FormattingString
    # -- the return value of calling ParameterizingString
    zero = pstr(0)
    for proto_num in range(pickle.HIGHEST_PROTOCOL):
        assert zero == pickle.loads(pickle.dumps(zero, protocol=proto_num))
    w.send(zero)
    r.recv() == zero

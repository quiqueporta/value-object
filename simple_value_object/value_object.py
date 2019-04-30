import inspect
from inspect import getargspec

from .exceptions import (
    ArgWithoutValueException,
    CannotBeChangeException,
    InvariantReturnValueException,
    NotDeclaredArgsException,
    ViolatedInvariantException
)

MIN_NUMBER_ARGS = 1


class ValueObject(object):

    def __new__(cls, *args, **kwargs):
        self = super(ValueObject, cls).__new__(cls)

        args_spec = ArgsSpec(self.__init__)

        def check_class_are_initialized():
            init_constructor_without_arguments = len(args_spec.args) <= MIN_NUMBER_ARGS
            if init_constructor_without_arguments:
                raise NotDeclaredArgsException()
            if None in args:
                raise ArgWithoutValueException()

        def replace_mutable_kwargs_with_immutable_types():
            for arg, value in kwargs.items():
                if isinstance(value, dict):
                    kwargs[arg] = immutable_dict(value)
                if isinstance(value, (list, set)):
                    kwargs[arg] = tuple(value)

        def assign_instance_arguments():
            assign_default_values()
            override_default_values_with_args()

        def assign_default_values():
            defaults = () if not args_spec.defaults else args_spec.defaults
            self.__dict__.update(
                dict(zip(args_spec.args[:0:-1], defaults[::-1]))
            )

        def override_default_values_with_args():
            self.__dict__.update(
                dict(list(zip(args_spec.args[1:], args)) + list(kwargs.items()))
            )

        def check_invariants():
            for invariant in obtain_invariants():
                if not invariant_execute(invariant):
                    raise ViolatedInvariantException(
                        'Args values {} violates invariant: {}'.format(
                            list(self.__dict__.values()), invariant
                        )
                    )

        def invariant_execute(invariant):
            return_value = invariant(self, self)

            if not isinstance(return_value, bool):
                raise InvariantReturnValueException()

            return return_value

        def is_invariant(method):
            try:
                return 'invariant_func_wrapper' in str(method) and '__init__' not in str(method)
            except TypeError:
                return False

        def obtain_invariants():
            invariants = [member[1] for member in inspect.getmembers(cls, is_invariant)]
            for invariant in invariants:
                yield invariant

        check_class_are_initialized()
        replace_mutable_kwargs_with_immutable_types()
        assign_instance_arguments()
        check_invariants()

        return self

    def __setattr__(self, name, value):
        raise CannotBeChangeException()

    def __eq__(self, other):
        if other is None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return self.__dict__ != other.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        args_spec = ArgsSpec(self.__init__)
        args_values = ["{}={}".format(arg, getattr(self, arg)) for arg in args_spec.args[1:]]

        return "{}({})".format(self.__class__.__name__, ", ".join(args_values))

    def __hash__(self):
        return self.hash

    @property
    def hash(self):
        return hash(repr(self))


class ArgsSpec(object):

    def __init__(self, method):
        try:
            self._args, self._varargs, self._keywords, self._defaults = getargspec(method)
        except TypeError:
            raise NotDeclaredArgsException()

    @property
    def args(self):
        return self._args

    @property
    def varargs(self):
        return self._varargs

    @property
    def keywords(self):
        return self._keywords

    @property
    def defaults(self):
        return self._defaults


class immutable_dict(dict):

    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kwargs):
        raise CannotBeChangeException()

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable

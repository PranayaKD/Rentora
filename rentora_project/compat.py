"""
Rentora Django Version Compatibility Layer.
Ensures seamless operation across Django 4.2, 5.0, 5.1, and 5.2+.

Specifically handles:
- Django 5.1+ CheckConstraint argument transition from check= to condition=
"""
import inspect
from django.db.models.constraints import CheckConstraint

_orig_check_constraint_init = getattr(CheckConstraint, '_rentora_orig_init', CheckConstraint.__init__)

def _compatible_check_constraint_init(self, *args, **kwargs):
    sig = inspect.signature(_orig_check_constraint_init)
    if 'condition' in sig.parameters and 'check' not in sig.parameters:
        # Django 5.1+ / 5.2+: expects condition=
        if 'check' in kwargs and 'condition' not in kwargs:
            kwargs['condition'] = kwargs.pop('check')
    elif 'check' in sig.parameters and 'condition' not in sig.parameters:
        # Django <5.1: expects check=
        if 'condition' in kwargs and 'check' not in kwargs:
            kwargs['check'] = kwargs.pop('condition')
    return _orig_check_constraint_init(self, *args, **kwargs)

if not hasattr(CheckConstraint, '_rentora_patched'):
    CheckConstraint._rentora_orig_init = _orig_check_constraint_init
    CheckConstraint.__init__ = _compatible_check_constraint_init
    CheckConstraint._rentora_patched = True

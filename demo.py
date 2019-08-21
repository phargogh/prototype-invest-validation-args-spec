mport logging
import os

import sympy
import sympy.parsing.sympy_parser
from osgeo import gdal, osr

LOGGER = logging.getLogger(__name__)

WORKSPACE_SPEC = {
    "type": "directory",
    "required": True,
    "validation_options": {
        "exists": True,
        "permissions": "rwx",
    }
}

SUFFIX_SPEC = {
    "type": "freestyle_string",
    "required": False,
    "validation_options": {
        "regexp": {
            "pattern": "[a-zA-Z0-9_-]*",
            "case_sensitive": False,
        }
    }
}

N_WORKERS_SPEC = {
    "type": "number",
    "required": False,
    "validation_options": {
        "regexp": {
            "pattern": "-?[0-9]+",
            "case_sensitive": False
        },
        "expression": "value >= -1"
    }
}

MODEL_SPEC = {
    "model_name": "Demonstration of the model Spec",
    "module": __name__,
    "userguide_html": "demo.html",
    "args": {
        "workspace_dir": WORKSPACE_SPEC,
        "results_suffix": SUFFIX_SPEC,
        "n_workers": N_WORKERS_SPEC,
        "info_table_path": {
            "type": "csv",
            "required": True,
            "validation_options": {
                "required_fields": ["NAME", "PATH", "STRESSOR_BUFFER"],
            }
        },
        "criteria_table_path": {
            "type": "csv",
            "required": True,
        },
        "resolution": {
            "type": "number",
            "required": True,
            "validation_options": {
                "expression": "value > 0",
            }
        },
        "max_rating": {
            "type": "number",
            "required": True,
            "validation_options": {
                "expression": "value > 0",
            }
        },
        "decay_eq": {
            "type": "options_string",
            "required": True,
            "validation_options": {
                "options": ["None", "Linear", "Exponential"],
            }
        },
        "aoi_vector_path": {
            "type": "vector",
            "required": True,
            "validation_options": {
                "layer_geometry_type": "polygon",
                "projected": True,
                "projected_units": "m",
            }
        },
        "visualize_outputs": {
            "type": "boolean",
            "required": True,
        }
    }
}

def validate_directory(dirpath, exists=False, permissions='rx'):
    if exists:
        if not os.path.exists(dirpath):
            return "Directory not found"

    if not os.path.isdir(dirpath):
        return "Path is not a directory"

    permissions_warning = validate_permissions(dirpath, permissions)
    if permissions_warning:
        return permissions_warning


def validate_file(filepath, permissions='r'):
    if not os.path.exists(filepath):
        return "File not found"

    permissions_warning = validate_permissions(filepath, permissions)
    if permissions_warning:
        return permissions_warning

def validate_permissions(path, permissions)
    for letter, mode, descriptor in (
            ('r', os.R_OK, 'read'),
            ('w', os.W_OK, 'write'),
            ('x', os.X_OK, 'execute')):
        if letter in permissions and not os.access(path, mode):
            return 'You must have %s access to this file' % descriptor

def validate_before(func):
    def decorator(*pre_validation_funcs):
        def wrapped_validator(*validation_args, **validation_kwargs):
            for pre_validator, validator_kwargs in pre_validation_funcs:
                warning_string = pre_validation_func(
                    *validation_args, **validator_kwargs)
                if warning_string:
                    return warning_string

            return func(*validation_args, **validation_kwargs)


def _check_projection(srs, projected, projection_units):
    if projected:
        if not srs.IsProjected():
            return "Vector must be projected in linear units."

    if projected_units:
        valid_meter_units = set('m', 'meter', 'meters', 'metre', 'metres')
        layer_units_name = srs.GetLinearUnitsName().lower()

        if projected_units in valid_meter_units:
            if not layer_units_name in valid_meter_units:
                return "Layer must be projected in meters"
        else:
            if not layer_units_name != projected_units:
                return "Layer must be projected in %s" % projected_units

    return None


@validate_before((validate_file, {'permissions': 'r'}))
def validate_raster(filepath, projected=False, projection_units=None):
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    gdal_dataset = gdal.OpenEx(filepath, gdal.OF_RASTER)
    gdal.PopErrorHandler()

    if gdal_dataset is None:
        return "File could not be opened as a GDAL raster"
    else:
        gdal_dataset = None

    srs = osr.SpatialReference()
    srs.ImportFromWkt(gdal_dataset.GetProjection())

    projection_warning = _check_projected(srs, projected, projection_units)
    if projection_warning:
        return projection_warning

    return None


@validate_before((validate_file, {'permissions': 'r'}))
def validate_vector(filepath, required_fields=None, projected=False,
                    projected_units=None):
    gdal.PushErrorHandler('CPLQuietErrorHandler')
    gdal_dataset = gdal.OpenEx(filepath, gdal.OF_VECTOR)
    gdal.PopErrorHandler()

    if gdal_dataset is None:
        return "File could not be opened as a GDAL vector"

    fieldnames = set([defn.GetName().upper() for defn in layer.schema])
    missing_fields = fieldnames - set(field.upper() for field in required_fields)
    if missing_fields:
        return "Fields are missing from the first layer: %s" % sorted(
            missing_fields)

    layer = gdal_dataset.GetLayer()
    srs = layer.GetSpatialRef()

    projection_warning = _check_projected(srs, projected, projection_units)
    if projection_warning:
        return projection_warning

    return None


def validate_freestyle_string(value, regexp=None):
    try:
        str(value):
    except (ValueError, TypeError):
        return "Could not convert value to a string"

    if regexp:
        flags = 0
        if 'case_sensitive' in regexp:
            if regexp['case_sensitive']:
                flags = re.IGNORECASE
        matches = re.findall(regexp['pattern'], str(value), flags)
        if not matches:
            return "Value did not match expected pattern %s", regexp['pattern']

    return None


def validate_option_string(value, options):
    if value not in options:
        return "Value must be one of: %s" % sorted(options)


def validate_number(value, regexp=None, expression=None):
    try:
        float(value)
    except (TypeError, ValueError):
        return "Value could not be interpreted as a number"

    if expression:
        # Check to make sure that 'value' is in the expression.
        if 'value' not in sympy.parsing.sympy_parser.parse_expr(
                expression).free_symbols:
            raise AssertionError('Value is not used in this expression')

        # Expression is assumed to return a boolean, something like
        # "value > 0" or "(value >= 0) & (value < 1)".  An exception will
        # be raised if sympy can't evaluate the expression.
        if not sympy.lambdify(['value'], expression, 'numpy')(value):
            return "Value does not meet condition %s" % expression

    return None


def validate_boolean(value):
    value = value.strip()
    if isinstance(str, value):
        if value.lower() not in ("true", "false"):
            return "Value must be one of 'True' or 'False'"

    else:
        try:
            bool(value)
        except (ValueError, TypeError):
            return "Value could not be cast to a boolean."

    return None



VALIDATION_FUNCS = {
    'file': validate_file,
    'folder': validate_directory,
    'csv': validate_csv,
    'raster': validate_raster,
    'vector': validate_vector,
    'number': validate_number,
    'boolean': validate_boolean,
    'freestyle_string': validate_freestyle_string,
    'option_string': validate_option_string,
}


def _do_the_validation(args, spec):
    validation_warnings = []

    # step 1: check absolute requirement
    missing_keys = set()
    keys_with_no_value = set()
    conditionally_required_keys = set()
    for key, parameter_spec in spec.items():
        if parameter_spec['required'] is True:
            if key not in args:
                missing_keys.add(key)
            else:
                if args[key] in ('', None):
                    keys_with_no_value.add(key)
        elif isinstance(parameter_spec['required'], str):
            conditionally_required_keys.add(key)

    if missing_keys:
        validation_warnings.append(
            (sorted(missing_keys), "Key is missing from the args dict"))

    if keys_with_no_value:
        validation_warnings.append(
            (sorted(keys_with_no_value), "Key is required but has no value"))

    invalid_keys = missing_keys + keys_with_no_value

    # step 2: check primitive validity
    for key, parameter_spec in spec.items():
        if key in invalid_keys:
            continue  # no need to validate a key we know is missing.

        type_validation_func = VALIDATION_FUNCS[parameter_spec['type']]
        try:
            warning_msg = type_validation_func(
                args[key], **parameter_spec['validation_options'])

            if warning_msg:
                validation_warnings.append(([key], warning_msg))
                invalid_keys.add(key)
        except Exception as error:
            LOGGER.exception('Error when validating key %s with value %s')
            validation_warnings.append(
                ([key], 'An unexpected error occurred in validation'))

    # step 3: check conditional requirement
    for key in conditionally_required_keys:
        if key in invalid_keys:
            continue  # no need to check requirement on already invalid input

        # An input is conditionally required when any of the upstream keys have
        # a value and are valid.
        for upstream_key in spec[key]['required']:
            if upstream_key not in invalid_keys:
                # It's required!
                if key not in args:
                    validation_warnings.append(
                        ([key], "Key is missing from the args dict"))
                else:
                    if args[key] in ('', None):
                        validation_warnings.append(
                            ([key], "Key is required but has no value"))

# Remaining work on this:
#  * Test this overarching functionality
#  * Test each of the individual validation functions
#  * Document the validation functions
#  * Add ARGS_SPEC to each of the models (in the CLI PR)


def validate(args):
    return []

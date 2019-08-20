import logging
import os

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
        "pattern": "[a-zA-Z0-9_-]*",
        "case_sensitive": False,
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

def validate_file(filepath, permissions):
    if not os.path.exists(filepath):
        return "File not found"

    for letter, mode, descriptor in (
            ('r', os.R_OK, 'read'),
            ('w', os.W_OK, 'write'),
            ('x', os.X_OK, 'execute')):
        if letter in permissions and not os.access(filepath, mode):
            return 'You must have %s access to this file' % descriptor

def validate_raster(filepath):
    file_warning = validate_file(filepath, 'r')
    gdal_dataset = gdal.OpenEx(filepath, gdal.OF_RASTER)
    if gdal_dataset is None:
        return "File could not be opened as a GDAL raster"
    else:
        gdal_dataset = None
    return None

def validate_vector(filepath, required_fields, projected=False,
                    projected_units=None):
    file_warning = validate_file(filepath, 'r')
    gdal_dataset = gdal.OpenEx(filepath, gdal.OF_VECTOR)
    if gdal_dataset is None:
        return "File could not be opened as a GDAL vector"

    layer = gdal_dataset.GetLayer()
    srs = layer.GetSpatialRef()
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


VALIDATION_FUNCS = {
    'csv': validate_csv,
    'raster': validate_raster,
    'vector': validate_vector,
    'file': validate_file,
}

def _do_the_validation(args, spec):
    validation_warnings = []

    # step 1: check absolute requirement
    missing_keys = set()
    keys_with_no_value = set()
    for key, parameter_spec in spec.items():
        if parameter_spec['required'] is True:
            if key not in args:
                missing_keys.add(key)
            else:
                if args[key] in ('', None):
                    keys_with_no_value.add(key)

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





def validate(args):
    return []

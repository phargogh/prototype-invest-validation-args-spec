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

def validate(args):
    return []

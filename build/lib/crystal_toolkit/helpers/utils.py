from crystal_toolkit import _DEFAULTS

def update_object_args(d_args, object_name, allowed_args):
    """Read dafault properties and overwrite them if user input exists
    
    Arguments:
        d_args {dict} -- User defined properties
        object_name {str} -- Name of object
        allowed_kwargs {List[str]} -- Used to limit the data that is passed to pythreejs
    
    Returns:
        Dictionary -- Properties of object after userinput and default values are considered
    """
    obj_args = {
        k: v
        for k, v in (_DEFAULTS['scene'][object_name] or {}).items()
    }
    obj_args.update({
        k: v
        for k, v in (d_args or {}).items() if k in allowed_args and v != None
    })
    return obj_args
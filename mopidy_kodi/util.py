import logging

def make_uri(_type, id=None, **params):
    if params:
        param_str =  "&".join("{}={}".format(k, v) for k, v in params.items())
    else:
        param_str = ''
    return 'kodi:/{}{}{}'.format(_type,
                                 '/{}'.format(id) if id else '',
                                 '?' + param_str if param_str else '')

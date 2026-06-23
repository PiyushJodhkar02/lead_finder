try:
    raise KeyError(' "fit_score"')
except Exception as e:
    print(f'Type: {type(e)}, Str: {e}')
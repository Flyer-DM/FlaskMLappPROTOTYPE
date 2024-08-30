import os


def cleanup():
    files = os.listdir(clear_dir := './datasets')
    for file in files:
        if file.startswith('temp'):
            if file.endswith('.csv'):
                os.remove(f'{clear_dir}/{file}')

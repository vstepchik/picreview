def sizeof_fmt(bytes_size: int, suffix: str = 'B') -> str:
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(bytes_size) < 1024.0:
            return f"{bytes_size:.0f}{unit}{suffix}" if unit == '' else f"{bytes_size:.2f}{unit}{suffix}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f}Yi{suffix}"

import openai
import os
import csv


# Description: Utility functions for the project

# Description: This function parses a time string in the format 'mm:ss.s' to seconds.
def parse_time(value):
    # if value is already a number, return it
    if (not value) or isinstance(value, (int, float)):
        return value

    try:
        return float(value)
    except:
        pass
    
    (minutes, seconds) = str(value).split(':')
    return int(minutes) * 60 + float(seconds)


def format_time(seconds, decimal_places=1, use_separator=True):
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    sep = ':' if use_separator else ''
    if decimal_places == 0:
        return f'{minutes:02d}{sep}{seconds:02.0f}'
    
    dot = '.' if use_separator else ''
    width = decimal_places + 3  # 3 = 2 (整数位) + 1 (小数点)
    return f'{minutes:02d}{sep}{seconds:0{width}.{decimal_places}f}'.replace('.', dot)


#!/usr/bin/env python3
"""
This module parses a formatted file of activities throughout the day and
classifies each time partition as Worthy, Rest or Neither.
"""
import os.path
import re
import sqlite3
from datetime import timedelta

# Get Regex
with open('worthy.regex') as file:
    WORTHY_REGEX = file.readlines()
    WORTHY_REGEX = [regex.strip() for regex in WORTHY_REGEX]
with open('rest.regex') as file:
    REST_REGEX = file.readlines()
    REST_REGEX = [regex.strip() for regex in REST_REGEX]
with open('neither.regex') as file:
    NEITHER_REGEX = file.readlines()
    NEITHER_REGEX = [regex.strip() for regex in NEITHER_REGEX]

def _timedelta_to_string(time):
    """
    Returns HH:MM format string from given timedelta
    """
    return str(time.seconds // 3600).zfill(2) + ':' + \
        str((time.seconds // 60) % 60).zfill(2)

def _get_timedelta_from_string(string):
    """
    Return timedelta from HH:MM formatted string
    """
    hour, minute = string.split(':')
    return timedelta(hours=int(hour), minutes=int(minute))

def _log_unclassified(line):
    """
    Appends given line to a log for later review
    """
    with open('unclassified.log', 'a+') as log:
        log.write(line + '\n')

def _parse_actions(line, actions):
    """
    Return 'W' (Worthy), 'N' (Neither), 'R' (Rest), 'X' (Unclassified) after
    classifying given actions with regex. If 'X' (Unclassified), the line is
    logged for review.
    """
    for regex in WORTHY_REGEX:
        for action in actions:
            if re.search(regex, action):
                return 'W'

    for regex in NEITHER_REGEX:
        for action in actions:
            if re.search(regex, action):
                return 'N'

    for regex in REST_REGEX:
        for action in actions:
            if re.search(regex, action):
                return 'R'

    _log_unclassified(line)
    return 'X'

def _save_to_db(date_str, worthy_str, rest_str, neither_str):
    """
    Save given date_str, worthy_str, rest_str and neither_str to a SQLite 3
    database.
    """
    if not os.path.exists('db.sqlite3'):
        # Create DB
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute((
            'CREATE TABLE record (date_str text, worthy text'
            ', rest text, neither text)'))
        print('Created new database.')
    else:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()

    # Insert Data
    cursor.execute('INSERT INTO record VALUES (?, ?, ?, ?)'
                   , [date_str, worthy_str, rest_str, neither_str])

    conn.commit()
    conn.close()

    print('Saved to database.')

def parse_file(filename):
    """
    Parse a file with given filename to classify activities.
    """
    # Get Data
    with open(filename, encoding='utf-8') as input_file:
        lines = input_file.readlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line[0] != '#']

    date_str = input('What is the date (YYYY-MM-DD)?')

    # Parse
    previous_time = timedelta(0)
    worthy_time = timedelta(0)
    rest_time = timedelta(0)
    neither_time = timedelta(0)
    # Whether the time is after 12:59 and should be converted to 24-hour format
    is_pm = False


    for line in lines:
        # Check if the line is a PM token ('~')
        if line[0] == '~':
            is_pm = True
            continue

        # Parse time
        time_str = line[0:5].strip()
        this_time = _get_timedelta_from_string(time_str)

        # Calculate timedelta
        delta_time = this_time - previous_time
        previous_time = this_time

        # If after 12:59, add 12 hours to make it 24-hour format
        if is_pm:
            delta_time += timedelta(hours=12)

        # Parse actions
        tokens = line[5:].split('/')
        tokens = [token.strip() for token in tokens]

        # Classify actions
        result = _parse_actions(line, tokens)
        if result == 'W':
            worthy_time += delta_time
        elif result == 'R':
            rest_time += delta_time
        elif result == 'N':
            neither_time += delta_time
        else:
            # Ask user
            while True:
                print(line)
                answer = input(
                    'Should the event above be marked W, R or N? (W, R, N): ')
                if answer == 'W':
                    worthy_time += delta_time
                    break
                elif answer == 'R':
                    rest_time += delta_time
                    break
                elif answer == 'N':
                    neither_time = delta_time
                    break
                else:
                    print((
                        'Unrecognized output: type W for worthy, R for rest,'
                        ' or N for neither'
                    ))

    worthy_str = _timedelta_to_string(worthy_time)
    rest_str = _timedelta_to_string(rest_time)
    neither_str = _timedelta_to_string(neither_time)

    print('Worthy  : ' + worthy_str)
    print('Rest    : ' + rest_str)
    print('Neither : ' + neither_str)

    # Save to SQLite3 Database
    _save_to_db(date_str, worthy_str, rest_str, neither_str)

    # TODO Dummy Data
    return {
        'date': date_str,
        'summary': [
            {'label': 'Worthy', 'duration': '540'},
            {'label': 'Rest', 'duration': '180'},
            {'label': 'Neither', 'duration': '480'}
        ],
        'worthy_list': [
            {'label': 'Something', 'duration': '330'},
            {'label': 'More Something', 'duration': '210'}
        ],
        'rest_list': [
            {'label': 'Another', 'duration': '90'},
            {'label': 'and More', 'duration': '90'}
        ],
        'neither_list': [
            {'label': 'Sleep', 'duration': '480'}
        ]
    }
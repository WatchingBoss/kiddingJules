import csv
import os
from collections import defaultdict
from dataclasses import dataclass

# A dataclass automatically generates __init__, __repr__, etc.
@dataclass
class LogEntry:
    user_id: int
    timestamp: str
    action: str
    product_id: str
    price: float

def process_logs(file_path):
    """
    Reads and processes the log file.
    """
    log_entries = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Use removeprefix() for cleaner string manipulation (new in 3.9)
            action = row['action'].removeprefix('action:')

            # Convert data types before creating the dataclass instance
            log_entries.append(LogEntry(
                user_id=int(row['user_id']),
                timestamp=row['timestamp'],
                action=action,
                product_id=row['product_id'],
                price=float(row['price']) if row['price'] else 0.0
            ))
    return log_entries

def analyze_logs(log_entries):
    """
    Performs a simple analysis of the log entries.
    """
    action_counts = defaultdict(int)
    total_revenue = 0.0
    for entry in log_entries:
        action_counts[entry.action] += 1
        if entry.action == 'purchase':
            total_revenue += entry.price

    return action_counts, total_revenue

def print_summary(action_counts, total_revenue, config=None):
    """
    Prints a summary of the analysis based on a config dictionary.
    """
    if config is None:
        config = {}

    title = config.get('title', 'Activity Summary')

    if (num_actions := len(action_counts)) > 0:
        print(f'--- {title} ({num_actions} types) ---')
        # Dictionaries in Python 3.6+ are insertion-ordered, but we still sort here
        # for deterministic output, which is good practice.
        for action, count in sorted(action_counts.items()):
            print(f'Action: "{action}", Count: {count}')

    if config.get('show_revenue', True):
        print('\n--- Revenue ---')
        print(f'Total Revenue: ${total_revenue:.2f}')


if __name__ == '__main__':
    # Construct the path to the data file relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '../data/user_activity.csv')

    # Python 3.9 Dictionary Merge Operator Example
    default_config = {'show_revenue': True, 'title': 'Activity Summary'}
    # Example of a user override. The right-hand dict's values take precedence.
    user_config = {'title': 'User Activity Report'}

    # In Python 3.9, we can merge dicts cleanly with the | operator
    final_config = default_config | user_config

    entries = process_logs(data_path)
    counts, revenue = analyze_logs(entries)
    print_summary(counts, revenue, config=final_config)

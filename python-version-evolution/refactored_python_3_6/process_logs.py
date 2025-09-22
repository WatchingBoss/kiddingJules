import csv
import os
from collections import defaultdict

# A simple class to hold log entry data
class LogEntry:
    def __init__(self, user_id, timestamp, action, product_id, price):
        self.user_id = int(user_id)
        self.timestamp = timestamp
        self.action = action
        self.product_id = product_id
        self.price = float(price) if price else 0.0

    def __repr__(self):
        return f'LogEntry(user_id={self.user_id}, action={self.action}, price={self.price})'

def process_logs(file_path):
    """
    Reads and processes the log file.
    """
    log_entries = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Data cleaning for older action format
            action = row['action']
            if action.startswith('action:'):
                action = action.split(':')[1]

            log_entries.append(LogEntry(
                user_id=row['user_id'],
                timestamp=row['timestamp'],
                action=action,
                product_id=row['product_id'],
                price=row['price']
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

def print_summary(action_counts, total_revenue):
    """
    Prints a summary of the analysis.
    """
    print('--- Activity Summary ---')
    # Dictionaries in Python 3.6+ are insertion-ordered, but we still sort here
    # for deterministic output, which is good practice.
    for action, count in sorted(action_counts.items()):
        print(f'Action: "{action}", Count: {count}')

    print('\n--- Revenue ---')
    print(f'Total Revenue: ${total_revenue:.2f}')


if __name__ == '__main__':
    # Construct the path to the data file relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '../data/user_activity.csv')

    entries = process_logs(data_path)
    counts, revenue = analyze_logs(entries)
    print_summary(counts, revenue)

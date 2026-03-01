import json
import random
import time
import sys

try:
    import pika
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing dependency. Please install required packages: {e}")
    sys.exit(1)

def main():
    # Initialize Faker for mock data generation
    fake = Faker()

    # Predefined lists for realistic data
    genres = ["Fiction", "Non-fiction", "Sci-Fi", "Fantasy", "Biography", "History", "Thriller", "Romance"]
    languages = ["English", "Spanish", "French", "German", "Italian", "Chinese", "Japanese"]

    # 1. Establish Connection
    print("Connecting to RabbitMQ at localhost...")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ broker: {e}")
        print("Ensure RabbitMQ is running locally on port 5672.")
        sys.exit(1)

    # 2. Declare Queue
    # Ensure the queue exists before publishing to it.
    # durable=True means messages survive RabbitMQ restarts.
    queue_name = 'books_queue'
    channel.queue_declare(queue=queue_name, durable=True)

    print(f" [*] Waiting to publish messages to '{queue_name}'. To exit press CTRL+C")

    # 3. Execution Loop
    try:
        while True:
            # Generate fake book data matching the schema
            book_data = {
                "title": fake.catch_phrase(),
                "year": random.randint(1900, 2023),
                "author": fake.name(),
                "genre": random.choice(genres),
                "language": random.choice(languages),
                "description": fake.text(max_nb_chars=500)
            }

            # Serialize to JSON string
            message_body = json.dumps(book_data)

            # Publish message to the queue
            # exchange='' uses the default exchange which routes directly to the queue with the routing_key
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_body
            )

            # Log to console concisely
            print(f" [x] Sent '{book_data['title']}' by {book_data['author']}")

            # Sleep for 1 second before generating the next message
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n [*] Exiting producer...")
    finally:
        # Clean up connection
        if 'connection' in locals() and connection.is_open:
            connection.close()

if __name__ == '__main__':
    main()

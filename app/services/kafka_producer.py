from kafka import KafkaProducer
import json

# שימי לב: בתוך Docker, אם הקונטיינר של האפליקציה פונה לקונטיינר של קפקה, 
# לפעמים צריך להשתמש בשם הקונטיינר או בכתובת המחשב המארח.
# בואי נתחיל עם 'localhost:9092' כמו שמופיע ב-Docker Desktop שלך.
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_message(topic, message):
    producer.send(topic, message)
    producer.flush()
    print(f"Sent: {message}")
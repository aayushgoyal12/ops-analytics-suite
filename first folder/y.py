from twilio.rest import Client

account_sid = "AC9df56bf33c7a6c9726ea2a0653be2c32"
auth_token = "44b6587199d06119356dbe2c6fcc4994"
client = Client(account_sid, auth_token)

message = client.messages.create(
    from_="whatsapp:+17372508034",
    to="whatsapp:+919650069743",
    body="Test message - automation pipeline check"
)

print(message.sid)
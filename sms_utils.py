import asyncio
import logging
from twilio.rest import Client
from config import settings

logger = logging.getLogger("restaurant")


def _send_sms_sync(to: str, body: str) -> None:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(to=to, from_=settings.TWILIO_FROM_NUMBER, body=body)


async def send_booking_sms(
    to_phone: str,
    customer_name: str,
    restaurant_name: str,
    booking_date: str,
    time_slot: str,
    guest_count: int,
    booking_id: str,
) -> None:
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER]):
        logger.warning("Twilio not configured — skipping SMS")
        return

    body = (
        f"Hi {customer_name}, your reservation is confirmed!\n"
        f"Restaurant: {restaurant_name}\n"
        f"Date: {booking_date} at {time_slot}\n"
        f"Guests: {guest_count}\n"
        f"Booking ID: {booking_id}\n"
        f"To cancel, use your Booking ID + phone number on the website."
    )

    try:
        await asyncio.to_thread(_send_sms_sync, to_phone, body)
        logger.info(f"SMS sent to {to_phone} for booking {booking_id}")
    except Exception as e:
        logger.error(f"SMS failed for booking {booking_id}: {e}")

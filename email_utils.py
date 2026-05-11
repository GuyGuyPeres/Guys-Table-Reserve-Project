import logging
import html as html_lib
import boto3
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger("restaurant")


def send_booking_confirmation(
    customer_email: str,
    customer_name: str,
    restaurant_name: str,
    booking_date: str,
    time_slot: str,
    guest_count: int,
    booking_id: str,
):
    if not settings.SES_SENDER_EMAIL:
        logger.warning("SES_SENDER_EMAIL not set — skipping confirmation email")
        return

    safe_name       = html_lib.escape(customer_name)
    safe_restaurant = html_lib.escape(restaurant_name)
    safe_date       = html_lib.escape(booking_date)
    safe_time       = html_lib.escape(time_slot)
    safe_id         = html_lib.escape(booking_id)

    plain_text = f"""Hello {customer_name},

Your reservation has been confirmed!

  Restaurant: {restaurant_name}
  Date:       {booking_date}
  Time:       {time_slot}
  Guests:     {guest_count}
  Booking ID: {booking_id}

Need to cancel? Visit the site and enter your Booking ID and phone number.

See you soon,
Guy's Table Reserve
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

          <!-- HEADER -->
          <tr>
            <td style="background:#0c0d0f;padding:36px 40px;text-align:center;">
              <p style="margin:0 0 4px 0;font-size:11px;letter-spacing:3px;color:#c9a84c;text-transform:uppercase;">Guy's Table Reserve</p>
              <h1 style="margin:0;font-size:26px;font-weight:normal;color:#ffffff;letter-spacing:1px;">Reservation <em style="color:#c9a84c;">Confirmed</em></h1>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="padding:36px 40px;">
              <p style="margin:0 0 24px 0;font-size:16px;color:#333;line-height:1.6;">
                Hello <strong>{safe_name}</strong>,<br>
                Your table has been successfully reserved. We look forward to welcoming you.
              </p>

              <!-- DETAILS BOX -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f6f0;border-left:4px solid #c9a84c;border-radius:4px;margin-bottom:28px;">
                <tr>
                  <td style="padding:24px 28px;">
                    <table width="100%" cellpadding="6" cellspacing="0">
                      <tr>
                        <td style="font-size:12px;letter-spacing:2px;color:#999;text-transform:uppercase;width:120px;">Restaurant</td>
                        <td style="font-size:15px;color:#1a1a1a;font-weight:bold;">{safe_restaurant}</td>
                      </tr>
                      <tr>
                        <td style="font-size:12px;letter-spacing:2px;color:#999;text-transform:uppercase;">Date</td>
                        <td style="font-size:15px;color:#1a1a1a;">{safe_date}</td>
                      </tr>
                      <tr>
                        <td style="font-size:12px;letter-spacing:2px;color:#999;text-transform:uppercase;">Time</td>
                        <td style="font-size:15px;color:#1a1a1a;">{safe_time}</td>
                      </tr>
                      <tr>
                        <td style="font-size:12px;letter-spacing:2px;color:#999;text-transform:uppercase;">Guests</td>
                        <td style="font-size:15px;color:#1a1a1a;">{guest_count}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- BOOKING ID -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#0c0d0f;border-radius:4px;margin-bottom:28px;">
                <tr>
                  <td style="padding:16px 24px;">
                    <p style="margin:0 0 4px 0;font-size:11px;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;">Booking ID</p>
                    <p style="margin:0;font-size:13px;color:#ffffff;font-family:monospace;letter-spacing:1px;">{safe_id}</p>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:13px;color:#888;line-height:1.6;">
                Need to cancel? Visit the site, scroll to <em>Cancel Your Reservation</em>, and enter your Booking ID and phone number.
              </p>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#f0ece4;padding:20px 40px;text-align:center;border-top:1px solid #e0d8c8;">
              <p style="margin:0;font-size:12px;color:#999;">&copy; 2026 Guy's Table Reserve. All rights reserved.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    try:
        ses = boto3.client("ses", region_name=settings.SES_REGION or "us-east-1")
        ses.send_email(
            Source=settings.SES_SENDER_EMAIL,
            Destination={"ToAddresses": [customer_email]},
            Message={
                "Subject": {"Data": f"Reservation Confirmed — {restaurant_name}"},
                "Body": {
                    "Text": {"Data": plain_text},
                    "Html": {"Data": html},
                },
            },
        )
        logger.info(f"Confirmation email sent to {customer_email} for booking {booking_id}")
    except ClientError as e:
        logger.error(f"SES error for booking {booking_id}: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email for booking {booking_id}: {e}")
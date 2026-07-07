# medbutton

## Automated reminders for taking medication twice a day

**REQUIRES MANUAL SETUP OF PINPOINT SMS NUMBER AND IOT BUTTON**

## Installation

1. Installs into an AWS account using `terraform`. Uses remote state, but no state locking.
2. Load into the Lambda control panel via the AWS Console and set up a new IoT button trigger.
3. Follow the instructions for uploading the certs and endpoint info for your specific button.
4. Go into SNS console and verify the phone numbers, if needed.

## Usage

- **IoT Button**: Press the physical button to log a med push.
- **SMS**: Text "PUSH" to the SNS phone number to log a med push (same as pressing the button).
- **Reminders**: If no push is detected by the morning (11 AM ET) or evening (9 PM ET) deadline, an SMS reminder is sent to all subscribed phones.
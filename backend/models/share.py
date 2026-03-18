"""Request and response models for newsletter email sharing."""

from pydantic import BaseModel


class SendToSelfRequest(BaseModel):
    """Request to send a newsletter edition to the logged-in user's email.

    Attributes:
        edition_id: MongoDB ObjectId string of the edition to send.
    """

    edition_id: str


class ShareEmailResponse(BaseModel):
    """Response returned after a send-to-self attempt.

    Attributes:
        success: Whether the email was sent successfully.
        message: Human-readable status message.
    """

    success: bool
    message: str

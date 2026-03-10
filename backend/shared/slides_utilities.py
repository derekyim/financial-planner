"""Utility class for creating and editing Google Slides presentations.

Uses the Google Slides API v1 via google-api-python-client with service
account credentials (same credentials used for Sheets).

When the service account has Drive storage, new presentations are created
as files in a ``financial_presentations`` folder.  When storage is
unavailable (common on consumer GCP projects), we fall back to clearing
and renaming the presentation at GOOGLE_SLIDES_URL.
"""

import logging
import os
import re
import uuid
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

FOLDER_NAME = "financial_presentations"
log = logging.getLogger(__name__)


class SlidesUtilities:
    """Wrapper around the Google Slides API for adding slides to a presentation."""

    SCOPES = [
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, credentials_path: str):
        credentials = Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        self.service = build("slides", "v1", credentials=credentials)
        self.drive_service = build("drive", "v3", credentials=credentials)
        self._folder_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_presentation(self, title: str) -> tuple[str, str]:
        """Create (or prepare) a presentation with the given *title*.

        1. Tries to create a brand-new file via Drive API.
        2. If the SA has no Drive storage, falls back to resetting the
           existing presentation pointed to by ``GOOGLE_SLIDES_URL``.

        Returns ``(presentation_id, url)``.
        """
        try:
            return self._create_new_presentation(title)
        except HttpError as exc:
            if "storageQuotaExceeded" in str(exc):
                log.warning(
                    "Drive storage quota exceeded — falling back to "
                    "resetting GOOGLE_SLIDES_URL presentation."
                )
                return self._reset_existing_presentation(title)
            raise

    @staticmethod
    def extract_presentation_id(url: str) -> str:
        match = re.search(r"/presentation/d/([a-zA-Z0-9_-]+)", url)
        if not match:
            raise ValueError(f"Could not extract presentation ID from URL: {url}")
        return match.group(1)

    def get_slide_count(self, presentation_id: str) -> int:
        pres = (
            self.service.presentations()
            .get(presentationId=presentation_id)
            .execute()
        )
        return len(pres.get("slides", []))

    def add_title_slide(
        self,
        presentation_id: str,
        title: str,
        subtitle: str = "",
    ) -> str:
        """Add a title slide at the end.  Returns the new slide's object ID."""
        slide_id = f"slide_{uuid.uuid4().hex[:12]}"
        insertion_index = self.get_slide_count(presentation_id)

        requests: list[dict] = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": str(insertion_index),
                    "slideLayoutReference": {"predefinedLayout": "TITLE"},
                }
            }
        ]
        self.service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

        text_requests = self._insert_placeholder_text(
            presentation_id, slide_id, title, subtitle
        )
        if text_requests:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": text_requests},
            ).execute()

        return slide_id

    def add_content_slide(
        self,
        presentation_id: str,
        title: str,
        body: str,
    ) -> str:
        """Add a slide with a title and body text.  Returns the slide ID."""
        slide_id = f"slide_{uuid.uuid4().hex[:12]}"
        title_id = f"title_{uuid.uuid4().hex[:12]}"
        body_id = f"body_{uuid.uuid4().hex[:12]}"
        insertion_index = self.get_slide_count(presentation_id)

        requests: list[dict] = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": str(insertion_index),
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            },
            {
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": 60, "unit": "PT"},
                            "width": {"magnitude": 648, "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": 36, "translateY": 20, "unit": "PT",
                        },
                    },
                }
            },
            {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
            {
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": {"bold": True, "fontSize": {"magnitude": 28, "unit": "PT"}},
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize",
                }
            },
            {
                "createShape": {
                    "objectId": body_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": 360, "unit": "PT"},
                            "width": {"magnitude": 648, "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": 36, "translateY": 90, "unit": "PT",
                        },
                    },
                }
            },
            {"insertText": {"objectId": body_id, "insertionIndex": 0, "text": body}},
            {
                "updateTextStyle": {
                    "objectId": body_id,
                    "style": {"fontSize": {"magnitude": 16, "unit": "PT"}},
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize",
                }
            },
        ]

        self.service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()
        return slide_id

    def add_bullet_slide(
        self,
        presentation_id: str,
        title: str,
        bullets: list[str],
    ) -> str:
        """Add a slide with a title and bullet points.  Returns the slide ID."""
        body_text = "\n".join(f"• {b}" for b in bullets)
        return self.add_content_slide(presentation_id, title, body_text)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_create_folder(self) -> str:
        """Find or create the ``financial_presentations`` folder in Drive."""
        if self._folder_id:
            return self._folder_id

        query = (
            f"name = '{FOLDER_NAME}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        results = (
            self.drive_service.files()
            .list(q=query, fields="files(id, name)", pageSize=1)
            .execute()
        )
        files = results.get("files", [])

        if files:
            self._folder_id = files[0]["id"]
        else:
            folder_meta = {
                "name": FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = (
                self.drive_service.files()
                .create(body=folder_meta, fields="id")
                .execute()
            )
            self._folder_id = folder["id"]
            self._share_with_user(self._folder_id)

        return self._folder_id

    def _share_with_user(self, file_id: str) -> None:
        """Share a file/folder with ``EMAIL_TO_SHARE_SLIDES_TO`` if set."""
        share_email = os.getenv("EMAIL_TO_SHARE_SLIDES_TO", "")
        if share_email:
            self.drive_service.permissions().create(
                fileId=file_id,
                body={
                    "type": "user",
                    "role": "writer",
                    "emailAddress": share_email,
                },
                fields="id",
                sendNotificationEmail=False,
            ).execute()
        else:
            self.drive_service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()

    def _create_new_presentation(self, title: str) -> tuple[str, str]:
        """Create a brand-new presentation file via Drive API."""
        folder_id = self._get_or_create_folder()
        file_meta = {
            "name": title,
            "mimeType": "application/vnd.google-apps.presentation",
            "parents": [folder_id],
        }
        created = (
            self.drive_service.files()
            .create(body=file_meta, fields="id")
            .execute()
        )
        pres_id = created["id"]
        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
        self._share_with_user(pres_id)
        return pres_id, url

    def _reset_existing_presentation(self, title: str) -> tuple[str, str]:
        """Clear all slides from GOOGLE_SLIDES_URL and rename it."""
        slides_url = os.getenv("GOOGLE_SLIDES_URL", "")
        if not slides_url:
            raise RuntimeError(
                "Cannot create new presentations (service account has no "
                "Drive storage) and GOOGLE_SLIDES_URL is not set.  Set "
                "GOOGLE_SLIDES_URL to a presentation shared with the "
                "service account as Editor."
            )
        pres_id = self.extract_presentation_id(slides_url)
        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"

        pres = (
            self.service.presentations()
            .get(presentationId=pres_id)
            .execute()
        )
        old_slide_ids = [s["objectId"] for s in pres.get("slides", [])]

        placeholder_id = f"slide_{uuid.uuid4().hex[:12]}"
        create_req: list[dict] = [
            {
                "createSlide": {
                    "objectId": placeholder_id,
                    "insertionIndex": "0",
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            }
        ]
        self.service.presentations().batchUpdate(
            presentationId=pres_id, body={"requests": create_req}
        ).execute()

        if old_slide_ids:
            delete_reqs: list[dict] = [
                {"deleteObject": {"objectId": sid}} for sid in old_slide_ids
            ]
            self.service.presentations().batchUpdate(
                presentationId=pres_id, body={"requests": delete_reqs}
            ).execute()

        self.drive_service.files().update(
            fileId=pres_id,
            body={"name": title},
            fields="id,name",
        ).execute()

        log.info("Reset presentation %s → '%s'", pres_id, title)
        return pres_id, url

    def _insert_placeholder_text(
        self,
        presentation_id: str,
        slide_id: str,
        title: str,
        subtitle: str,
    ) -> list[dict]:
        """Find placeholder elements on a layout-based slide and insert text."""
        pres = (
            self.service.presentations()
            .get(presentationId=presentation_id)
            .execute()
        )
        requests: list[dict] = []
        for slide in pres.get("slides", []):
            if slide["objectId"] != slide_id:
                continue
            for elem in slide.get("pageElements", []):
                ph = elem.get("shape", {}).get("placeholder", {})
                ph_type = ph.get("type", "")
                obj_id = elem["objectId"]
                if ph_type in ("CENTER_TITLE", "TITLE"):
                    requests.append(
                        {
                            "insertText": {
                                "objectId": obj_id,
                                "insertionIndex": 0,
                                "text": title,
                            }
                        }
                    )
                elif ph_type == "SUBTITLE" and subtitle:
                    requests.append(
                        {
                            "insertText": {
                                "objectId": obj_id,
                                "insertionIndex": 0,
                                "text": subtitle,
                            }
                        }
                    )
        return requests
